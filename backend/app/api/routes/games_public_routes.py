"""Public games endpoints (safe for anonymous traffic)."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.games_response_cache import games_response_cache
from app.core.dependencies import get_db
from app.models.game import Game
from app.models.watched_game import WatchedGame
from app.schemas.game import GameResponse, GamesListResponse
from app.services.game_listing_window_service import get_listing_window_for_sport_state
from app.services.odds_fetcher import OddsFetcherService
from app.services.sport_state_policy import get_policy_for_sport
from app.services.sport_state_service import get_sport_state
from app.services.sports_config import get_sport_config
from app.utils.nfl_week import calculate_nfl_week, get_available_weeks, get_current_nfl_week
from app.utils.timezone_utils import TimezoneNormalizer

router = APIRouter()


def _status_label_for_state(sport_state: str) -> str:
    if sport_state == "IN_BREAK":
        return "League break"
    if sport_state == "OFFSEASON":
        return "Offseason"
    if sport_state == "PRESEASON":
        return "Preseason"
    if sport_state == "POSTSEASON":
        return "Postseason"
    if sport_state == "IN_SEASON":
        return "In season"
    return "Not in season"


def _filter_games_by_window(
    games: List[GameResponse],
    window_start_utc: datetime,
    window_end_utc: datetime,
) -> List[GameResponse]:
    out: List[GameResponse] = []
    for g in games:
        st = TimezoneNormalizer.ensure_utc(g.start_time)
        if window_start_utc <= st <= window_end_utc:
            out.append(g)
    return out


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


@router.get("/sports/{sport}/games", response_model=GamesListResponse)
async def get_games_for_sport(
    sport: str,
    db: AsyncSession = Depends(get_db),
    refresh: bool = Query(False, description="Bypass server cache (does not force external odds refresh)"),
    week: Optional[int] = Query(
        None,
        ge=1,
        le=22,
        description="NFL week number (1-18 regular season, 19-22 postseason). Only applies to NFL.",
    ),
):
    """
    Get upcoming games with odds for the requested sport.
    Response is clamped by sport state: OFFSEASON returns empty list (no far-future games).

    IMPORTANT: `refresh=true` bypasses only the server's in-memory cache. It does NOT
    force a The Odds API call (to preserve credits).
    """
    start_time = time.time()
    sport_config = get_sport_config(sport)
    cache_key = f"{sport_config.slug}_week_{week}" if week else sport_config.slug
    now = datetime.now(timezone.utc)

    state_result = await get_sport_state(db, sport_config.code, now=now)
    sport_state = state_result["sport_state"]
    next_game_at = state_result.get("next_game_at")
    days_to_next = state_result.get("days_to_next")
    preseason_enable_days = state_result.get("preseason_enable_days")
    status_label = _status_label_for_state(sport_state)
    policy = get_policy_for_sport(sport_config.code)
    window = get_listing_window_for_sport_state(sport_state, now, policy=policy)

    def _meta() -> dict:
        return {
            "sport_state": sport_state,
            "next_game_at": next_game_at,
            "status_label": status_label,
            "days_to_next": days_to_next,
            "preseason_enable_days": preseason_enable_days,
        }

    if window is None:
        print(f"[GAMES] {sport_config.display_name} OFFSEASON: returning empty list (no far-future games)")
        return GamesListResponse(games=[], **_meta())

    if not refresh:
        cached_games = games_response_cache.get(cache_key)
        if cached_games is not None:
            elapsed = time.time() - start_time
            cache_age = games_response_cache.age_seconds(cache_key) or 0.0
            filtered = _filter_games_by_window(cached_games, window.start_utc, window.end_utc)
            print(
                f"[GAMES] Cached {sport_config.display_name} -> {len(filtered)} in window (age: {cache_age:.0f}s) in {elapsed:.2f}s"
            )
            return GamesListResponse(games=filtered, **_meta())

    try:
        fetcher = OddsFetcherService(db)
        games = await fetcher.get_or_fetch_games(sport_config.slug, force_refresh=False)
        elapsed = time.time() - start_time
        print(f"[GAMES] Fetched {len(games)} {sport_config.display_name} games in {elapsed:.2f}s")

        if not games:
            cached_games = games_response_cache.get(cache_key)
            if cached_games is not None:
                if week and sport_config.code == "NFL":
                    cached_games = [g for g in cached_games if g.week == week]
                filtered = _filter_games_by_window(cached_games, window.start_utc, window.end_utc)
                return GamesListResponse(games=filtered, **_meta())
            return GamesListResponse(games=[], **_meta())

        if week and sport_config.code == "NFL":
            games = [g for g in games if g.week == week]
        games_response_cache.set(cache_key, games)
        filtered = _filter_games_by_window(games, window.start_utc, window.end_utc)
        return GamesListResponse(games=filtered, **_meta())
    except Exception as e:
        import traceback

        error_detail = f"Failed to fetch {sport_config.display_name} games: {str(e)}"
        elapsed = time.time() - start_time
        print(f"[GAMES] ERROR after {elapsed:.2f}s: {error_detail}")
        print(traceback.format_exc())

        cached_games = games_response_cache.get(cache_key)
        if cached_games is not None:
            filtered = _filter_games_by_window(cached_games, window.start_utc, window.end_utc)
            return GamesListResponse(games=filtered, **_meta())

        try:
            print(f"[GAMES] Attempting simple database fallback for {sport_config.display_name}...")
            cutoff_time = now - timedelta(hours=24)
            future_cutoff = window.end_utc

            result = await db.execute(
                select(Game)
                .where(Game.sport == sport_config.code)
                .where(Game.start_time >= cutoff_time)
                .where(Game.start_time <= future_cutoff)
                .order_by(Game.start_time)
                .limit(sport_config.max_quick_games)
            )
            fallback_games = result.scalars().all()
            simple_response: List[GameResponse] = []
            for game in fallback_games:
                normalized_start = TimezoneNormalizer.ensure_utc(game.start_time)
                if not (window.start_utc <= normalized_start <= window.end_utc):
                    continue
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
            if simple_response:
                games_response_cache.set(cache_key, simple_response)
            return GamesListResponse(games=simple_response, **_meta())
        except Exception as fallback_error:
            print(f"[GAMES] Simple fallback also failed: {fallback_error}")
            import traceback
            traceback.print_exc()

        return GamesListResponse(games=[], **_meta())


@router.get("/sports/{sport}/games/quick", response_model=GamesListResponse)
async def get_games_quick(
    sport: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Quick endpoint - returns games without full odds data, clamped by sport-state listing window.
    """
    start_time = time.time()
    sport_config = get_sport_config(sport)
    now = datetime.now(timezone.utc)
    state_result = await get_sport_state(db, sport_config.code, now=now)
    sport_state = state_result["sport_state"]
    policy = get_policy_for_sport(sport_config.code)
    window = get_listing_window_for_sport_state(sport_state, now, policy=policy)
    status_label = _status_label_for_state(sport_state)
    next_game_at = state_result.get("next_game_at")

    if window is None:
        print(f"[GAMES_QUICK] {sport_config.display_name} OFFSEASON: empty list")
        return GamesListResponse(
            games=[],
            sport_state=sport_state,
            next_game_at=next_game_at,
            status_label=status_label,
            days_to_next=state_result.get("days_to_next"),
            preseason_enable_days=state_result.get("preseason_enable_days"),
        )

    try:
        result = await db.execute(
            select(Game)
            .where(Game.sport == sport_config.code)
            .where(Game.start_time >= window.start_utc)
            .where(Game.start_time <= window.end_utc)
            .where((Game.status.is_(None)) | (Game.status.notin_(["finished", "closed", "complete", "Final"])))
            .order_by(Game.start_time)
            .limit(sport_config.max_quick_games)
        )
        games = result.scalars().all()
        response: List[GameResponse] = []
        for game in games:
            normalized_start = TimezoneNormalizer.ensure_utc(game.start_time)
            response.append(GameResponse.model_validate({
                "id": str(game.id),
                "external_game_id": game.external_game_id,
                "sport": game.sport,
                "home_team": game.home_team,
                "away_team": game.away_team,
                "start_time": normalized_start,
                "status": game.status,
                "week": calculate_nfl_week(game.start_time) if game.sport == "NFL" else None,
                "markets": [],
            }))
        elapsed = time.time() - start_time
        print(f"[GAMES_QUICK] Returned {len(response)} {sport_config.display_name} games in {elapsed:.2f}s")
        return GamesListResponse(
            games=response,
            sport_state=sport_state,
            next_game_at=next_game_at,
            status_label=status_label,
            days_to_next=state_result.get("days_to_next"),
            preseason_enable_days=state_result.get("preseason_enable_days"),
        )
    except Exception as e:
        print(f"[GAMES_QUICK] Error: {e}")
        return GamesListResponse(
            games=[],
            sport_state=sport_state,
            next_game_at=next_game_at,
            status_label=status_label,
            days_to_next=state_result.get("days_to_next"),
            preseason_enable_days=state_result.get("preseason_enable_days"),
        )


@router.post("/games/{game_id}/watch")
async def watch_game(
    game_id: str,
    user_id: str = Query(..., description="User identifier (simple string for now)"),
    db: AsyncSession = Depends(get_db),
):
    """Add a game to user's watchlist."""
    from uuid import UUID
    
    try:
        game_uuid = UUID(game_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid game ID")
    
    # Check if already watched
    result = await db.execute(
        select(WatchedGame).where(
            WatchedGame.user_id == user_id,
            WatchedGame.game_id == game_uuid,
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return {"ok": True, "message": "Game already in watchlist"}
    
    # Add to watchlist
    watched = WatchedGame(user_id=user_id, game_id=game_uuid)
    db.add(watched)
    await db.commit()
    
    return {"ok": True, "message": "Game added to watchlist"}


@router.delete("/games/{game_id}/watch")
async def unwatch_game(
    game_id: str,
    user_id: str = Query(..., description="User identifier"),
    db: AsyncSession = Depends(get_db),
):
    """Remove a game from user's watchlist."""
    from uuid import UUID
    
    try:
        game_uuid = UUID(game_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid game ID")
    
    result = await db.execute(
        select(WatchedGame).where(
            WatchedGame.user_id == user_id,
            WatchedGame.game_id == game_uuid,
        )
    )
    watched = result.scalar_one_or_none()
    
    if not watched:
        return {"ok": True, "message": "Game not in watchlist"}
    
    await db.delete(watched)
    await db.commit()
    
    return {"ok": True, "message": "Game removed from watchlist"}


@router.get("/user/{user_id}/watchlist", response_model=List[GameResponse])
async def get_watchlist(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get user's watchlist of games."""
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(WatchedGame)
        .where(WatchedGame.user_id == user_id)
        .options(selectinload(WatchedGame.game))
        .order_by(WatchedGame.created_at.desc())
    )
    watched_games = result.scalars().all()
    
    if not watched_games:
        return []
    
    # Convert to GameResponse
    from app.services.game_response_converter import GameResponseConverter
    converter = GameResponseConverter()
    games = [wg.game for wg in watched_games if wg.game]
    return converter.to_response(games)


@router.get("/analytics/top-edges")
async def get_top_edges(
    sport: Optional[str] = Query(None, description="Filter by sport (NFL, NBA, etc.)"),
    limit: int = Query(10, ge=1, le=50, description="Number of edges to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get top betting edges based on confidence and model vs market difference."""
    from app.models.game_analysis import GameAnalysis
    from app.models.game import Game
    from datetime import datetime, timedelta
    
    # Query analyses with high confidence
    now = datetime.utcnow()
    cutoff = now + timedelta(days=7)  # Only upcoming games
    
    query = (
        select(GameAnalysis, Game)
        .join(Game, GameAnalysis.game_id == Game.id)
        .where(Game.start_time >= now)
        .where(Game.start_time <= cutoff)
        .where(Game.status.notin_(["finished", "closed", "complete", "Final"]))
    )
    
    if sport:
        query = query.where(Game.sport == sport.upper())
    
    result = await db.execute(query)
    analyses = result.all()
    
    edges = []
    for analysis, game in analyses:
        content = analysis.analysis_content or {}
        confidence_breakdown = content.get("confidence_breakdown", {})
        confidence_total = confidence_breakdown.get("confidence_total", 0)
        
        # Calculate model edge
        model_probs = content.get("model_win_probability", {})
        odds_snapshot = content.get("odds_snapshot", {})
        
        home_model_prob = model_probs.get("home_win_prob", 0.5)
        home_market_prob = odds_snapshot.get("home_implied_prob", 0.5)
        
        # Normalize market prob
        away_market_prob = odds_snapshot.get("away_implied_prob", 0.5)
        market_total = home_market_prob + away_market_prob
        if market_total > 0:
            home_market_prob = home_market_prob / market_total
        
        model_edge = abs(home_model_prob - home_market_prob) * 100  # Convert to percentage
        
        # Score = confidence + edge
        edge_score = confidence_total + (model_edge * 2)
        
        edges.append({
            "game_id": str(game.id),
            "matchup": f"{game.away_team} @ {game.home_team}",
            "sport": game.sport,
            "start_time": game.start_time.isoformat() if hasattr(game.start_time, "isoformat") else str(game.start_time),
            "confidence_total": confidence_total,
            "model_edge_pct": round(model_edge, 1),
            "edge_score": round(edge_score, 1),
            "analysis_slug": analysis.slug,
        })
    
    # Sort by edge score (highest first)
    edges.sort(key=lambda x: x["edge_score"], reverse=True)
    
    return {
        "top_edges": edges[:limit],
        "count": len(edges[:limit]),
    }



