"""Analysis detail endpoint (per-game article).

This module delegates generation to `AnalysisOrchestratorService`, which
ensures a fast core response and background long-form generation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.dependencies import get_db
from app.core.dependencies import get_optional_user
from app.core.config import settings
from app.models.game import Game
from app.models.user import User
from app.schemas.analysis import GameAnalysisResponse
from app.services.analysis import AnalysisOrchestratorService
from app.services.analysis_content_normalizer import AnalysisContentNormalizer
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
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analysis: {e}")

    content = analysis.analysis_content or {}
    if not isinstance(content, dict):
        content = {}
    content = AnalysisContentNormalizer().normalize(content)

    game_time_result = await db.execute(select(Game.start_time).where(Game.id == analysis.game_id))
    game_time = game_time_result.scalar_one_or_none() or analysis.generated_at
    game_time = TimezoneNormalizer.ensure_utc(game_time)

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


