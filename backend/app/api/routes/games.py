"""Games API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time

from app.core.dependencies import get_db
from app.models.game import Game
from app.schemas.game import GameResponse
from app.services.odds_fetcher import OddsFetcherService
from app.services.sports_config import SportConfig, get_sport_config, list_supported_sports
from app.utils.nfl_week import (
    calculate_nfl_week, 
    get_current_nfl_week, 
    get_week_date_range, 
    get_available_weeks
)

router = APIRouter()

# Simple in-memory cache for games per sport (lasts 10 minutes for faster loads)
_games_cache: Dict[str, List[GameResponse]] = {}
_cache_timestamp: Dict[str, datetime] = {}
CACHE_TTL_SECONDS = 600  # 10 minutes for faster subsequent loads


def _get_cached_games(cache_key: str) -> Optional[List[GameResponse]]:
    """Return cached games for a specific sport if cache is still fresh."""
    cached = _games_cache.get(cache_key)
    timestamp = _cache_timestamp.get(cache_key)
    if not cached or not timestamp:
        return None
    cache_age = (datetime.now() - timestamp).total_seconds()
    if cache_age < CACHE_TTL_SECONDS:
        return cached
    return None


@router.get("/weeks/nfl", summary="Get NFL weeks info")
async def get_nfl_weeks():
    """
    Get information about NFL weeks including current week and available weeks.
    
    Returns:
        - current_week: Current NFL week number
        - weeks: List of all weeks with availability status
    """
    current_week = get_current_nfl_week()
    weeks = get_available_weeks()
    
    return {
        "current_week": current_week,
        "season_year": datetime.now().year if datetime.now().month >= 9 else datetime.now().year - 1,
        "weeks": weeks
    }


@router.get("/sports", summary="List supported sports")
async def list_sports():
    """Return metadata for all supported sports."""
    return [
        {
            "slug": config.slug,
            "code": config.code,
            "display_name": config.display_name,
            "default_markets": config.default_markets,
        }
        for config in list_supported_sports()
    ]


@router.get("/sports/{sport}/games", response_model=List[GameResponse])
async def get_games_for_sport(
    sport: str,
    db: AsyncSession = Depends(get_db),
    refresh: bool = Query(False, description="Force refresh from API"),
    week: Optional[int] = Query(None, ge=1, le=18, description="NFL week number (1-18). Only applies to NFL."),
):
    """
    Get upcoming games with odds for the requested sport.
    
    For NFL, you can filter by week number using the `week` query parameter.
    If no week is specified, returns all upcoming games.
    
    Returns cached games immediately if available (within 5 minutes),
    otherwise fetches from database or API.
    """
    start_time = time.time()
    sport_config = get_sport_config(sport)
    cache_key = f"{sport_config.slug}_week_{week}" if week else sport_config.slug
    print(f"[GAMES] {sport_config.display_name} request refresh={refresh} week={week}")
    
    if not refresh:
        cached_games = _get_cached_games(cache_key)
        if cached_games is not None:
            elapsed = time.time() - start_time
            cache_age = (datetime.now() - _cache_timestamp[cache_key]).total_seconds()
            print(f"[GAMES] Returning cached {sport_config.display_name} games (age: {cache_age:.0f}s) in {elapsed:.2f}s")
            return cached_games
    
    try:
        fetcher = OddsFetcherService(db)
        games = await fetcher.get_or_fetch_games(sport_config.slug, force_refresh=refresh)
        elapsed = time.time() - start_time
        print(f"[GAMES] Fetched {len(games)} {sport_config.display_name} games in {elapsed:.2f}s")
        
        if not games:
            cached_games = _get_cached_games(cache_key)
            if cached_games is not None:
                print(f"[GAMES] No new games, returning cached {len(cached_games)} entries")
                # Apply week filter to cached games too
                if week and sport_config.code == "NFL":
                    cached_games = [g for g in cached_games if g.week == week]
                return cached_games
            return []
        
        # Apply week filter for NFL if specified
        if week and sport_config.code == "NFL":
            games = [g for g in games if g.week == week]
            print(f"[GAMES] Filtered to {len(games)} games for week {week}")
        
        _games_cache[cache_key] = games
        _cache_timestamp[cache_key] = datetime.now()
        return games
    except Exception as e:
        import traceback
        error_detail = f"Failed to fetch {sport_config.display_name} games: {str(e)}"
        elapsed = time.time() - start_time
        print(f"[GAMES] ERROR after {elapsed:.2f}s: {error_detail}")
        print(traceback.format_exc())
        
        # Check cached games first
        cached_games = _get_cached_games(cache_key)
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
                # Convert to response format without relationships
                simple_response = []
                for game in fallback_games:
                    game_dict = {
                        "id": str(game.id),
                        "external_game_id": game.external_game_id,
                        "sport": game.sport,
                        "home_team": game.home_team,
                        "away_team": game.away_team,
                        "start_time": game.start_time,
                        "status": game.status,
                        "week": calculate_nfl_week(game.start_time) if game.sport == "NFL" else None,
                        "markets": [],  # Empty markets for fallback
                    }
                    simple_response.append(GameResponse.model_validate(game_dict))
                
                print(f"[GAMES] Fallback returned {len(simple_response)} games (without odds)")
                _games_cache[cache_key] = simple_response
                _cache_timestamp[cache_key] = datetime.now()
                return simple_response
        except Exception as fallback_error:
            print(f"[GAMES] Simple fallback also failed: {fallback_error}")
            import traceback
            traceback.print_exc()
        
        # Return empty array instead of raising error to prevent frontend crash
        print(f"[GAMES] All fallbacks failed, returning empty array")
        return []


@router.post("/sports/{sport}/games/refresh", summary="Manually refresh games from API")
async def refresh_games_for_sport(
    sport: str,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a refresh of games from The Odds API for a specific sport."""
    try:
        sport_config = get_sport_config(sport)
        fetcher = OddsFetcherService(db)
        games = await fetcher.get_or_fetch_games(sport_config.slug, force_refresh=True)
        
        # Clear cache to force fresh data on next request
        cache_key = sport_config.slug
        if cache_key in _games_cache:
            del _games_cache[cache_key]
        if cache_key in _cache_timestamp:
            del _cache_timestamp[cache_key]
        
        return {
            "success": True,
            "sport": sport_config.display_name,
            "games_count": len(games),
            "message": f"Refreshed {len(games)} {sport_config.display_name} games"
        }
    except Exception as e:
        import traceback
        error_detail = f"Failed to refresh {sport} games: {str(e)}"
        print(f"[REFRESH] ERROR: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/warmup", summary="Pre-warm cache for all sports")
async def warmup_cache(db: AsyncSession = Depends(get_db)):
    """
    Pre-warm the cache for all sports.
    Call this on app startup or periodically to ensure fast responses.
    """
    start_time = time.time()
    results = {}
    
    for sport_config in list_supported_sports():
        try:
            cache_key = sport_config.slug
            cached = _get_cached_games(cache_key)
            if cached is not None:
                results[sport_config.slug] = {
                    "status": "cached",
                    "count": len(cached)
                }
                continue
            
            fetcher = OddsFetcherService(db)
            games = await fetcher.get_or_fetch_games(sport_config.slug, force_refresh=False)
            _games_cache[cache_key] = games
            _cache_timestamp[cache_key] = datetime.now()
            results[sport_config.slug] = {
                "status": "fetched",
                "count": len(games)
            }
        except Exception as e:
            results[sport_config.slug] = {
                "status": "error",
                "error": str(e)
            }
    
    elapsed = time.time() - start_time
    return {
        "success": True,
        "elapsed_seconds": round(elapsed, 2),
        "sports": results
    }


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
        # Only show games from the past 24 hours (for live/recent games)
        # and upcoming games within lookahead days
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
        games = result.scalars().all()
        
        if not games:
            return []
        
        response = []
        for game in games:
            game_dict = {
                "id": str(game.id),
                "external_game_id": game.external_game_id,
                "sport": game.sport,
                "home_team": game.home_team,
                "away_team": game.away_team,
                "start_time": game.start_time,
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

