"""Public games endpoints (safe for anonymous traffic)."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.games_response_cache import games_response_cache
from app.core.dependencies import get_db
from app.models.game import Game
from app.schemas.game import GameResponse
from app.services.odds_fetcher import OddsFetcherService
from app.services.sports_config import get_sport_config
from app.utils.nfl_week import calculate_nfl_week, get_available_weeks, get_current_nfl_week
from app.utils.timezone_utils import TimezoneNormalizer

router = APIRouter()


@router.get("/weeks/nfl", summary="Get NFL weeks info")
async def get_nfl_weeks(db: AsyncSession = Depends(get_db)):
    """
    Get information about NFL weeks including current week and available weeks.
    
    Weeks are marked as available if:
    1. They are current or future (not past), within 2 weeks ahead, OR
    2. Games actually exist in the database for that week (even in off-season)

    Returns:
        - current_week: Current NFL week number
        - weeks: List of all weeks with availability status
    """
    from datetime import timezone as tz
    from sqlalchemy import select
    
    current_week = get_current_nfl_week()
    weeks = get_available_weeks()
    
    # Check if games exist for each week and mark as available if they do
    # This ensures weeks show up even in off-season if games are loaded
    for week_info in weeks:
        week_num = week_info["week"]
        week_start_str = week_info.get("start_date")
        week_end_str = week_info.get("end_date")
        
        if week_start_str and week_end_str:
            try:
                # Parse ISO format datetime strings (they should be timezone-aware from get_week_date_range)
                # Handle both 'Z' suffix and '+00:00' format
                if week_start_str.endswith('Z'):
                    week_start_str = week_start_str.replace('Z', '+00:00')
                if week_end_str.endswith('Z'):
                    week_end_str = week_end_str.replace('Z', '+00:00')
                
                week_start = datetime.fromisoformat(week_start_str)
                week_end = datetime.fromisoformat(week_end_str)
                
                # Ensure timezone-aware (should already be, but be safe)
                if week_start.tzinfo is None:
                    week_start = week_start.replace(tzinfo=tz.utc)
                if week_end.tzinfo is None:
                    week_end = week_end.replace(tzinfo=tz.utc)
                
                # Check if games exist for this week
                scheduled_statuses = ("scheduled", "status_scheduled")
                result = await db.execute(
                    select(Game)
                    .where(Game.sport == "NFL")
                    .where(Game.start_time >= week_start)
                    .where(Game.start_time <= week_end)
                    .where(or_(Game.status.is_(None), func.lower(Game.status).in_(scheduled_statuses)))
                    .limit(1)
                )
                games_exist = result.scalar_one_or_none() is not None
                
                # If games exist, mark week as available (even if it's off-season or outside normal window)
                if games_exist:
                    week_info["is_available"] = True
            except Exception as e:
                # If date parsing fails, skip this check (non-critical)
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Error checking games for week {week_num}: {e}")
                pass

    return {
        "current_week": current_week,
        "season_year": datetime.now().year if datetime.now().month >= 9 else datetime.now().year - 1,
        "weeks": weeks,
    }


@router.get("/sports/{sport}/games", response_model=List[GameResponse])
async def get_games_for_sport(
    sport: str,
    db: AsyncSession = Depends(get_db),
    refresh: bool = Query(False, description="Bypass server cache (does not force external odds refresh)"),
    week: Optional[int] = Query(None, ge=1, le=18, description="NFL week number (1-18). Only applies to NFL."),
):
    """
    Get upcoming games with odds for the requested sport.

    IMPORTANT: `refresh=true` bypasses only the server's in-memory cache. It does NOT
    force a The Odds API call (to preserve credits).
    """
    start_time = time.time()
    sport_config = get_sport_config(sport)
    cache_key = f"{sport_config.slug}_week_{week}" if week else sport_config.slug
    print(f"[GAMES] {sport_config.display_name} request refresh={refresh} week={week}")

    if not refresh:
        cached_games = games_response_cache.get(cache_key)
        if cached_games is not None:
            elapsed = time.time() - start_time
            cache_age = games_response_cache.age_seconds(cache_key) or 0.0
            print(
                f"[GAMES] Returning cached {sport_config.display_name} games (age: {cache_age:.0f}s) in {elapsed:.2f}s"
            )
            return cached_games

    try:
        fetcher = OddsFetcherService(db)
        # Do NOT pass `refresh` through as `force_refresh` (would burn credits).
        games = await fetcher.get_or_fetch_games(sport_config.slug, force_refresh=False)
        elapsed = time.time() - start_time
        print(f"[GAMES] Fetched {len(games)} {sport_config.display_name} games in {elapsed:.2f}s")

        if not games:
            cached_games = games_response_cache.get(cache_key)
            if cached_games is not None:
                print(f"[GAMES] No new games, returning cached {len(cached_games)} entries")
                if week and sport_config.code == "NFL":
                    cached_games = [g for g in cached_games if g.week == week]
                return cached_games
            return []

        if week and sport_config.code == "NFL":
            games = [g for g in games if g.week == week]
            print(f"[GAMES] Filtered to {len(games)} games for week {week}")

        games_response_cache.set(cache_key, games)
        return games
    except Exception as e:
        import traceback

        error_detail = f"Failed to fetch {sport_config.display_name} games: {str(e)}"
        elapsed = time.time() - start_time
        print(f"[GAMES] ERROR after {elapsed:.2f}s: {error_detail}")
        print(traceback.format_exc())

        # Check cached games first
        cached_games = games_response_cache.get(cache_key)
        if cached_games is not None:
            print(f"[GAMES] Returning {len(cached_games)} cached games due to error")
            return cached_games

        # Try simple database query as fallback (without relationships to avoid errors)
        try:
            print(f"[GAMES] Attempting simple database fallback for {sport_config.display_name}...")
            now = datetime.utcnow()
            cutoff_time = now - timedelta(hours=24)
            future_cutoff = now + timedelta(days=sport_config.lookahead_days)

            result = await db.execute(
                select(Game)
                .where(Game.sport == sport_config.code)
                .where(Game.start_time >= cutoff_time)
                .where(Game.start_time <= future_cutoff)
                .order_by(Game.start_time)
                .limit(sport_config.max_quick_games)
            )
            fallback_games = result.scalars().all()

            if fallback_games:
                simple_response: List[GameResponse] = []
                for game in fallback_games:
                    normalized_start = TimezoneNormalizer.ensure_utc(game.start_time)
                    game_dict = {
                        "id": str(game.id),
                        "external_game_id": game.external_game_id,
                        "sport": game.sport,
                        "home_team": game.home_team,
                        "away_team": game.away_team,
                        "start_time": normalized_start,
                        "status": game.status,
                        "week": calculate_nfl_week(game.start_time) if game.sport == "NFL" else None,
                        "markets": [],
                    }
                    simple_response.append(GameResponse.model_validate(game_dict))

                print(f"[GAMES] Fallback returned {len(simple_response)} games (without odds)")
                games_response_cache.set(cache_key, simple_response)
                return simple_response
        except Exception as fallback_error:
            print(f"[GAMES] Simple fallback also failed: {fallback_error}")
            import traceback

            traceback.print_exc()

        # Return empty array instead of raising error to prevent frontend crash
        print("[GAMES] All fallbacks failed, returning empty array")
        return []


@router.get("/sports/{sport}/games/quick", response_model=List[GameResponse])
async def get_games_quick(
    sport: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Quick endpoint - returns games without full odds data for faster loading.
    """
    start_time = time.time()
    sport_config = get_sport_config(sport)
    print(f"[GAMES_QUICK] {sport_config.display_name} request started")

    try:
        now = datetime.utcnow()
        cutoff_time = now - timedelta(hours=24)
        future_cutoff = now + timedelta(days=sport_config.lookahead_days)

        result = await db.execute(
            select(Game)
            .where(Game.sport == sport_config.code)
            .where(Game.start_time >= cutoff_time)
            .where(Game.start_time <= future_cutoff)
            .where((Game.status.is_(None)) | (Game.status.notin_(["finished", "closed", "complete", "Final"])))
            .order_by(Game.start_time)
            .limit(sport_config.max_quick_games)
        )
        games = result.scalars().all()

        if not games:
            return []

        response: List[GameResponse] = []
        for game in games:
            normalized_start = TimezoneNormalizer.ensure_utc(game.start_time)
            game_dict = {
                "id": str(game.id),
                "external_game_id": game.external_game_id,
                "sport": game.sport,
                "home_team": game.home_team,
                "away_team": game.away_team,
                "start_time": normalized_start,
                "status": game.status,
                "week": calculate_nfl_week(game.start_time) if game.sport == "NFL" else None,
                "markets": [],
            }
            response.append(GameResponse.model_validate(game_dict))

        elapsed = time.time() - start_time
        print(f"[GAMES_QUICK] Returned {len(response)} {sport_config.display_name} games in {elapsed:.2f}s")
        return response
    except Exception as e:
        print(f"[GAMES_QUICK] Error: {e}")
        return []



