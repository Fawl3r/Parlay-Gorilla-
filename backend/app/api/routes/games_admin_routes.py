"""Admin-only games endpoints that can trigger heavy work."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.admin.auth import require_admin
from app.api.routes.games_response_cache import games_response_cache
from app.core.dependencies import get_db
from app.models.game import Game
from app.models.user import User
from app.services.game_time_corrector import GameTimeCorrector
from app.services.odds_api_rate_limiter import get_rate_limiter
from app.services.odds_fetcher import OddsFetcherService
from app.services.sports_config import get_sport_config, list_supported_sports
from app.utils.timezone_utils import TimezoneNormalizer

router = APIRouter()


@router.post("/sports/{sport}/games/refresh", summary="Manually refresh games from API (admin)")
async def refresh_games_for_sport(
    sport: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Manually trigger a refresh of games for a specific sport (admin-only)."""
    _ = admin  # unused; dependency enforces auth
    try:
        sport_config = get_sport_config(sport)
        fetcher = OddsFetcherService(db)
        games = await fetcher.get_or_fetch_games(sport_config.slug, force_refresh=True)

        # Clear in-process cache to serve fresh DB results immediately.
        games_response_cache.delete(sport_config.slug)

        return {
            "success": True,
            "sport": sport_config.display_name,
            "games_count": len(games),
            "message": f"Refreshed {len(games)} {sport_config.display_name} games",
        }
    except Exception as e:
        import traceback

        error_detail = f"Failed to refresh {sport} games: {str(e)}"
        print(f"[REFRESH] ERROR: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/games/refresh-all", summary="Force refresh all sports from API (admin)")
async def refresh_all_games(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    fix_times: bool = Query(False, description="Also fix game times using ESPN (runs in background)"),
):
    """
    Force refresh games for ALL sports.

    Admin-only because it can be expensive and, if misused, can burn external API credits.
    """
    _ = admin
    start_time = time.time()
    results = {}

    games_response_cache.clear()
    print("[REFRESH_ALL] Cleared in-process games cache")

    rate_limiter = get_rate_limiter()
    rate_limiter.clear_all_caches()
    print("[REFRESH_ALL] Cleared rate limiter cache and call times")

    all_sports = list_supported_sports()
    print(f"[REFRESH_ALL] Refreshing {len(all_sports)} sports...")

    for sport_config in all_sports:
        try:
            print(f"[REFRESH_ALL] Refreshing {sport_config.display_name}...")
            fetcher = OddsFetcherService(db)

            games = await fetcher.get_or_fetch_games(sport_config.slug, force_refresh=True)

            if fix_times and sport_config.code in ["NFL", "NBA", "NHL", "MLB", "MLS", "EPL", "LALIGA", "UCL", "SOCCER"]:
                async def _fix_times_background():
                    from app.database.session import AsyncSessionLocal

                    async with AsyncSessionLocal() as bg_db:
                        try:
                            corrector = GameTimeCorrector()
                            now = datetime.utcnow()
                            future_cutoff = now + timedelta(days=sport_config.lookahead_days)

                            result = await bg_db.execute(
                                select(Game)
                                .where(Game.sport == sport_config.code)
                                .where(Game.start_time >= now)
                                .where(Game.start_time <= future_cutoff)
                            )
                            db_games = result.scalars().all()

                            corrected_count = 0
                            for game in db_games:
                                try:
                                    corrected_time = await corrector.get_corrected_time(
                                        home_team=game.home_team,
                                        away_team=game.away_team,
                                        odds_time=game.start_time,
                                        sport_code=sport_config.code,
                                    )
                                    if corrected_time and corrected_time != game.start_time:
                                        time_diff_hours = abs(
                                            (game.start_time - corrected_time).total_seconds() / 3600.0
                                        )
                                        if time_diff_hours >= 6:
                                            game.start_time = TimezoneNormalizer.ensure_utc(corrected_time)
                                            corrected_count += 1
                                except Exception:
                                    continue

                            if corrected_count > 0:
                                await bg_db.commit()
                                print(f"[REFRESH_ALL] Fixed {corrected_count} {sport_config.display_name} game times")
                        except Exception as time_error:
                            print(f"[REFRESH_ALL] Time correction failed for {sport_config.display_name}: {time_error}")

                background_tasks.add_task(_fix_times_background)
                print(f"[REFRESH_ALL] Scheduled time correction for {sport_config.display_name} (background)")

            results[sport_config.slug] = {
                "status": "success",
                "games_count": len(games),
                "display_name": sport_config.display_name,
            }
            print(f"[REFRESH_ALL] ✓ {sport_config.display_name}: {len(games)} games")
        except Exception as e:
            import traceback

            error_msg = str(e)
            print(f"[REFRESH_ALL] ✗ {sport_config.display_name} failed: {error_msg}")
            print(traceback.format_exc())
            results[sport_config.slug] = {
                "status": "error",
                "error": error_msg,
                "display_name": sport_config.display_name,
            }

    elapsed = time.time() - start_time
    successful = sum(1 for r in results.values() if r.get("status") == "success")
    total_games = sum(r.get("games_count", 0) for r in results.values() if r.get("status") == "success")

    return {
        "success": True,
        "elapsed_seconds": round(elapsed, 2),
        "sports_refreshed": successful,
        "sports_total": len(all_sports),
        "total_games": total_games,
        "fix_times_applied": fix_times,
        "results": results,
        "message": f"Refreshed {successful}/{len(all_sports)} sports, {total_games} total games",
    }


