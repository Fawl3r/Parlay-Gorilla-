"""Analysis detail endpoint (per-game article).

This module delegates generation to `AnalysisOrchestratorService`, which
ensures a fast core response and background long-form generation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from datetime import date, timezone as tz

from app.core.dependencies import get_db
from app.core.dependencies import get_optional_user
from app.core.config import settings
from app.models.analysis_page_views import AnalysisPageViews
from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.models.user import User
from app.schemas.analysis import GameAnalysisResponse
from app.services.alerting.alerting_service import get_alerting_service
from app.services.analysis import AnalysisOrchestratorService
from app.services.analysis.analysis_repository import AnalysisRepository
from app.services.analysis_content_normalizer import AnalysisContentNormalizer
from app.utils.placeholders import is_placeholder_team
from app.utils.timezone_utils import TimezoneNormalizer

router = APIRouter()


@router.get("/analysis/{sport}/{slug:path}", response_model=GameAnalysisResponse)
async def get_analysis(
    sport: str,
    slug: str,
    refresh: bool = Query(False, description="Force regeneration of core analysis when incomplete"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get analysis for a game by slug.

    Example: /api/analysis/nfl/bears-vs-packers-week-14-2025
    """
    # Only admins may force a refresh. For everyone else, treat it as a no-op
    # to avoid user-driven regeneration storms.
    if refresh and not (current_user and current_user.is_admin()):
        refresh = False

    try:
        orchestrator = AnalysisOrchestratorService(db)
        result = await orchestrator.get_or_generate_for_slug(
            sport_identifier=sport,
            slug=slug,
            refresh=refresh,
            core_timeout_seconds=settings.analysis_core_timeout_seconds,
        )
        analysis = result.analysis
    except LookupError as e:
        # The DB can be cold (e.g., after deploy/scale-to-zero) and analysis slugs may come
        # from older clients/bookmarks. Before returning a hard 404, do a best-effort
        # warmup of games for this sport and retry once.
        try:
            from app.services.odds_fetcher import OddsFetcherService

            print(f"[Analysis API] LookupError for {sport}/{slug}; warming games and retrying once...")
            await OddsFetcherService(db).get_or_fetch_games(sport_identifier=sport, force_refresh=False)

            orchestrator = AnalysisOrchestratorService(db)
            result = await orchestrator.get_or_generate_for_slug(
                sport_identifier=sport,
                slug=slug,
                refresh=refresh,
                core_timeout_seconds=settings.analysis_core_timeout_seconds,
            )
            analysis = result.analysis
        except Exception:
            raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analysis: {e}")

    content = analysis.analysis_content or {}
    if not isinstance(content, dict):
        content = {}
    content = AnalysisContentNormalizer().normalize(content)

    game_row_result = await db.execute(select(Game).where(Game.id == analysis.game_id))
    game_row = game_row_result.scalar_one_or_none()
    game_time = game_row.start_time if game_row else analysis.generated_at
    game_time = TimezoneNormalizer.ensure_utc(game_time)

    # Alert when analysis detail is served with placeholder team names (TBD, AFC, etc.)
    if game_row and (
        is_placeholder_team(game_row.home_team) or is_placeholder_team(game_row.away_team)
    ):
        try:
            alerting = get_alerting_service()
            await alerting.emit(
                "analysis.teams.placeholder",
                "warning",
                {
                    "slug": str(analysis.slug),
                    "matchup": str(analysis.matchup),
                    "home_team": getattr(game_row, "home_team", None),
                    "away_team": getattr(game_row, "away_team", None),
                },
                sport=str(analysis.league or sport),
                next_action_hint="Run schedule repair or backfill; check API-Sports/ESPN.",
            )
        except Exception as alert_err:
            print(f"[Analysis API] Alert emit failed: {alert_err}")

    return GameAnalysisResponse(
        id=str(analysis.id),
        slug=str(analysis.slug),
        league=str(analysis.league),
        matchup=str(analysis.matchup),
        game_id=str(analysis.game_id),
        game_time=game_time,
        analysis_content=content,
        seo_metadata=analysis.seo_metadata,
        generated_at=TimezoneNormalizer.ensure_utc(analysis.generated_at),
        expires_at=TimezoneNormalizer.ensure_utc(analysis.expires_at) if analysis.expires_at else None,
        version=int(getattr(analysis, "version", 1) or 1),
    )


@router.post("/analysis/{sport}/{slug:path}/view")
async def increment_analysis_view(
    sport: str,
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Increment view count for an analysis page.
    
    Used for traffic-based props gating. Called from frontend on client-side only.
    """
    try:
        # Resolve slug to analysis
        repo = AnalysisRepository(db)
        league = sport.upper()
        full_slug = f"{sport.lower()}/{slug}"
        analysis = await repo.get_by_slug(league=league, slug=full_slug)
        
        if not analysis:
            # Analysis not found - return ok anyway to avoid breaking frontend
            return {"ok": True}
        
        # Get today's date bucket (UTC)
        today = date.today()
        
        # Upsert view count
        result = await db.execute(
            select(AnalysisPageViews).where(
                AnalysisPageViews.analysis_id == analysis.id,
                AnalysisPageViews.view_bucket_date == today,
            )
        )
        view_record = result.scalar_one_or_none()
        
        if view_record:
            view_record.views += 1
        else:
            view_record = AnalysisPageViews(
                analysis_id=analysis.id,
                game_id=analysis.game_id,
                league=analysis.league,
                slug=analysis.slug,
                view_bucket_date=today,
                views=1,
            )
            db.add(view_record)
        
        await db.commit()
        return {"ok": True}
    except Exception as e:
        # Never fail view tracking - log and return ok
        print(f"[Analysis View] Error tracking view: {e}")
        await db.rollback()
        return {"ok": True}

