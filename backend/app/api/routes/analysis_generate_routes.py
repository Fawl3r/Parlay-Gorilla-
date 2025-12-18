"""Analysis generation endpoints.

Separated from `analysis.py` to keep route modules small and focused.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.config import settings
from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.schemas.analysis import AnalysisGenerationRequest
from app.services.ai_text_normalizer import AiTextNormalizer
from app.services.analysis import AnalysisOrchestratorService
from app.services.data_fetchers.team_photos import TeamPhotoFetcher
from app.services.odds_fetcher import OddsFetcherService
from app.services.sports_config import get_sport_config
from app.services.analysis.analysis_repository import AnalysisRepository
from app.utils.nfl_week import calculate_nfl_week

router = APIRouter()


def _generate_slug(home_team: str, away_team: str, league: str, game_time: datetime) -> str:
    """Generate URL-friendly slug for analysis page."""
    home_clean = re.sub(r"[^a-z0-9]+", "-", home_team.lower()).strip("-")
    away_clean = re.sub(r"[^a-z0-9]+", "-", away_team.lower()).strip("-")

    if league == "NFL":
        week = calculate_nfl_week(game_time)
        return f"{league.lower()}/{away_clean}-vs-{home_clean}-week-{week}-{game_time.year}"

    date_str = game_time.strftime("%Y-%m-%d")
    return f"{league.lower()}/{away_clean}-vs-{home_clean}-{date_str}"


@router.post("/analysis/generate")
async def generate_analysis(
    request: AnalysisGenerationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate or regenerate analysis for a game.

    This endpoint triggers AI analysis generation. Use sparingly as it's expensive.
    """
    try:
        result = await db.execute(select(Game).where(Game.id == uuid.UUID(request.game_id)))
        game = result.scalar_one_or_none()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        existing_result = await db.execute(
            select(GameAnalysis).where(GameAnalysis.game_id == game.id)
        )
        existing = existing_result.scalar_one_or_none()

        repo = AnalysisRepository(db)
        if existing and not request.force_regenerate and repo.analysis_has_core(existing):
            return {
                "message": "Analysis already exists",
                "analysis_id": str(existing.id),
                "slug": existing.slug,
            }

        # Warm odds cache (non-blocking here; analysis generator will read from DB anyway)
        odds_fetcher = OddsFetcherService(db)
        sport_config = get_sport_config(game.sport.lower())
        await odds_fetcher.get_or_fetch_games(sport_config.slug, force_refresh=False)

        orchestrator = AnalysisOrchestratorService(db)
        analysis = await orchestrator.ensure_core_for_game(
            game=game,
            core_timeout_seconds=settings.analysis_core_timeout_seconds,
            force_regenerate=bool(request.force_regenerate),
        )
        if not analysis:
            raise HTTPException(status_code=500, detail="Failed to generate analysis")

        analysis_content = analysis.analysis_content or {}

        # Normalize any literal "\\n" sequences in long-form fields before storage.
        analysis_content = AiTextNormalizer().normalize_obj(analysis_content)

        return {
            "message": "Analysis generated successfully",
            "analysis_id": str(analysis.id),
            "slug": analysis.slug,
            "version": analysis.version,
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"[Analysis API] Error generating analysis: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")


# NOTE: Team photo route MUST come before /{slug:path} to avoid being captured
@router.get("/analysis/{sport}/team-photo")
async def get_team_photo(
    sport: str,
    team_name: str = Query(..., description="Team name (e.g., 'Miami Dolphins')"),
    opponent: Optional[str] = Query(
        None, description="Opponent team name (not used for stadium photos)"
    ),
):
    """
    Get multiple stadium photos for the home team for carousel display.

    Returns list of photo URLs (cached for 7 days to save API requests).
    """
    try:
        photo_fetcher = TeamPhotoFetcher()
        photo_urls = await photo_fetcher.get_team_action_photo(
            team_name=team_name,
            league=sport.upper(),
            opponent=opponent,
        )

        if photo_urls and len(photo_urls) > 0:
            return {
                "photo_urls": photo_urls,
                "photo_url": photo_urls[0],  # backward compatibility
                "team": team_name,
                "league": sport.upper(),
                "count": len(photo_urls),
            }

        return {
            "photo_urls": [],
            "photo_url": None,
            "team": team_name,
            "league": sport.upper(),
            "count": 0,
        }
    except Exception as e:
        print(f"[Team Photo API] Error fetching photos: {e}")
        return {
            "photo_urls": [],
            "photo_url": None,
            "team": team_name,
            "league": sport.upper(),
            "error": str(e),
        }



