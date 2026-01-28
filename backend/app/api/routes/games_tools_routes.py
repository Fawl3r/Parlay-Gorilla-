"""Operational/maintenance endpoints (admin-only where appropriate)."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.admin.auth import require_admin
from app.api.routes.games_response_cache import games_response_cache
from app.core.dependencies import get_db
from app.models.game import Game
from app.models.game_results import GameResult
from app.models.user import User
from app.schemas.game import GameResponse
from app.services.ats_ou_calculator import ATSOUCalculator
from app.services.game_time_corrector import GameTimeCorrector
from app.services.odds_api_rate_limiter import get_rate_limiter
from app.services.odds_fetcher import OddsFetcherService
from app.services.sports_config import get_sport_config, list_supported_sports
from app.utils.nfl_week import calculate_nfl_week
from app.utils.timezone_utils import TimezoneNormalizer

router = APIRouter()


@router.post("/sports/{sport}/games/fix-placeholders", summary="Fix games with placeholder team names (AFC/NFC) using ESPN (admin)")
async def fix_placeholder_team_names(
    sport: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Fix existing games that have placeholder team names by matching with ESPN games."""
    _ = admin
    try:
        sport_config = get_sport_config(sport)
        
        from app.services.odds_fetcher import OddsFetcherService
        fetcher = OddsFetcherService(db)
        
        now = datetime.utcnow()
        future_cutoff = now + timedelta(days=sport_config.lookahead_days)
        
        await fetcher._fix_placeholder_team_names(sport_config, now, future_cutoff)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Attempted to fix placeholder team names for {sport_config.display_name}",
            "sport": sport_config.code,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fixing placeholder team names: {str(e)}")


@router.post("/sports/{sport}/games/fix-times", summary="Fix game start times using ESPN (admin)")
async def fix_game_times(
    sport: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    _ = admin
    try:
        sport_config = get_sport_config(sport)

        supported_sports = ["NFL", "NBA", "NHL", "MLB", "MLS", "EPL", "LALIGA", "UCL", "SOCCER"]
        if sport_config.code not in supported_sports:
            raise HTTPException(
                status_code=400,
                detail=f"Time correction not supported for {sport_config.display_name}. Supported: {', '.join(supported_sports)}",
            )

        corrector = GameTimeCorrector()
        now = datetime.utcnow()
        future_cutoff = now + timedelta(days=sport_config.lookahead_days)

        result = await db.execute(
            select(Game)
            .where(Game.sport == sport_config.code)
            .where(Game.start_time >= now)
            .where(Game.start_time <= future_cutoff)
            .order_by(Game.start_time)
        )
        games = result.scalars().all()

        corrected_count = 0
        corrections = []

        for game in games:
            try:
                corrected_time = await corrector.get_corrected_time(
                    home_team=game.home_team,
                    away_team=game.away_team,
                    odds_time=game.start_time,
                    sport_code=sport_config.code,
                )

                if corrected_time and corrected_time != game.start_time:
                    time_diff_hours = abs((game.start_time - corrected_time).total_seconds() / 3600.0)
                    if time_diff_hours >= 6:
                        old_time = game.start_time
                        game.start_time = TimezoneNormalizer.ensure_utc(corrected_time)
                        corrected_count += 1
                        corrections.append(
                            {
                                "game": f"{game.away_team} @ {game.home_team}",
                                "old_time": old_time.isoformat(),
                                "new_time": game.start_time.isoformat(),
                                "diff_hours": round(time_diff_hours, 1),
                            }
                        )
                        print(
                            f"[FIX_TIMES] Corrected {game.away_team} @ {game.home_team}: "
                            f"{old_time} -> {game.start_time} (diff: {time_diff_hours:.1f}h)"
                        )
            except Exception as e:
                print(f"[FIX_TIMES] Error correcting {game.away_team} @ {game.home_team}: {e}")
                continue

        if corrected_count > 0:
            await db.commit()

        games_response_cache.delete(sport_config.slug)

        return {
            "success": True,
            "sport": sport_config.display_name,
            "games_checked": len(games),
            "games_corrected": corrected_count,
            "corrections": corrections,
            "message": f"Corrected {corrected_count} of {len(games)} {sport_config.display_name} game times",
        }
    except Exception as e:
        await db.rollback()
        import traceback

        error_detail = f"Failed to fix {sport} game times: {str(e)}"
        print(f"[FIX_TIMES] ERROR: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/quota-status", summary="Get The Odds API quota status")
async def get_quota_status():
    rate_limiter = get_rate_limiter()
    status_info = rate_limiter.get_quota_status()

    # Note: Usage headers are best-effort; we primarily conserve via long TTL caching.
    return {
        "quota_remaining": status_info["remaining"],
        "quota_used": status_info["used"],
        "last_updated": status_info["last_updated"],
        "min_call_interval_hours": 48,
        "cache_ttl_hours": 48,
    }


@router.get("/warmup", summary="Pre-warm cache for all sports (admin)")
async def warmup_cache(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    _ = admin
    start_time = time.time()
    results = {}

    for sport_config in list_supported_sports():
        try:
            cache_key = sport_config.slug
            cached = games_response_cache.get(cache_key)
            if cached is not None:
                results[sport_config.slug] = {"status": "cached", "count": len(cached)}
                continue

            fetcher = OddsFetcherService(db)
            games = await fetcher.get_or_fetch_games(sport_config.slug, force_refresh=False)
            games_response_cache.set(cache_key, games)
            results[sport_config.slug] = {"status": "fetched", "count": len(games)}
        except Exception as e:
            results[sport_config.slug] = {"status": "error", "error": str(e)}

    elapsed = time.time() - start_time
    return {"success": True, "elapsed_seconds": round(elapsed, 2), "sports": results}


@router.post("/games/calculate-ats-ou", summary="Calculate ATS and Over/Under trends (admin)")
async def calculate_ats_ou_trends(
    sport: str = Query("NFL", description="Sport code: NFL, NBA, NHL, MLB, EPL, LALIGA, MLS, UCL, SOCCER"),
    season: str = Query("2025", description="Season year (e.g., '2025')"),
    season_type: str = Query("REG", description="Season type: REG, PRE, or PST (NFL/NBA/NHL)"),
    weeks: Optional[str] = Query(None, description="Comma-separated list of weeks (e.g., '1,2,3') or 'all'"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD (MLB/Soccer only)"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD (MLB/Soccer only)"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    _ = admin
    from datetime import datetime as dt

    start_time = time.time()
    try:
        week_list = None
        if weeks and weeks.lower() != "all":
            try:
                week_list = [int(w.strip()) for w in weeks.split(",")]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid weeks format. Use comma-separated numbers (e.g., '1,2,3') or 'all'",
                )

        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = dt.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        if end_date:
            try:
                end_dt = dt.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

        calculator = ATSOUCalculator(db, sport=sport)
        result = await calculator.calculate_season_trends(
            season=season,
            season_type=season_type,
            weeks=week_list,
            start_date=start_dt,
            end_date=end_dt,
        )

        elapsed = time.time() - start_time
        result["elapsed_seconds"] = round(elapsed, 2)

        return {"success": True, "message": f"ATS/OU trends calculated for {sport} {season} {season_type}", "sport": sport, **result}
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error calculating ATS/OU trends: {str(e)}")


@router.get("/games/backfill-progress", summary="Get backfill progress by sport and season (admin)")
async def get_backfill_progress(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    _ = admin
    stmt = (
        select(
            GameResult.sport,
            func.extract("year", GameResult.game_date).label("year"),
            func.count(GameResult.id).label("games_total"),
            func.count(GameResult.home_covered_spread).label("games_with_ats"),
            func.count(GameResult.total_over_under).label("games_with_ou"),
        )
        .group_by(GameResult.sport, func.extract("year", GameResult.game_date))
        .order_by(GameResult.sport, func.extract("year", GameResult.game_date))
    )

    result = await db.execute(stmt)

    progress: Dict[str, Dict[str, Dict[str, int]]] = {}
    totals = {"games_total": 0, "games_with_ats": 0, "games_with_ou": 0}

    for row in result.fetchall():
        sport_key = row.sport
        year = str(int(row.year))
        games_total = int(row.games_total or 0)
        games_with_ats = int(row.games_with_ats or 0)
        games_with_ou = int(row.games_with_ou or 0)

        progress.setdefault(sport_key, {})[year] = {
            "games_total": games_total,
            "games_with_ats": games_with_ats,
            "games_with_ou": games_with_ou,
        }

        totals["games_total"] += games_total
        totals["games_with_ats"] += games_with_ats
        totals["games_with_ou"] += games_with_ou

    return {"progress": progress, "totals": totals, "last_updated": datetime.utcnow().isoformat() + "Z"}


@router.post("/games/backfill-all-sports", summary="Backfill 2024 and 2025 data for all sports (admin)")
async def backfill_all_sports_data(
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
):
    _ = admin
    start_time = time.time()

    SPORTS_CONFIG = {
        "NFL": {"seasons": ["2024", "2025"], "season_type": "REG", "weeks": None},
        "NBA": {"seasons": ["2024", "2025"], "season_type": "REG", "weeks": None},
        "NHL": {"seasons": ["2024", "2025"], "season_type": "REG", "weeks": None},
        "MLB": {"seasons": ["2024", "2025"], "season_type": "REG", "start_date": None, "end_date": None},
        "EPL": {"seasons": ["2024", "2025"], "season_type": "REG", "start_date": None, "end_date": None},
        "MLS": {"seasons": ["2024", "2025"], "season_type": "REG", "start_date": None, "end_date": None},
    }

    def _run_backfill():
        import asyncio
        import threading
        from app.database.session import AsyncSessionLocal

        async def _perform_backfill():
            total_games = 0
            total_teams = set()
            results = {}

            async with AsyncSessionLocal() as inner_db:
                for sport_key, config in SPORTS_CONFIG.items():
                    try:
                        print(f"[BACKFILL] Processing {sport_key}...")
                        calculator = ATSOUCalculator(inner_db, sport=sport_key)

                        for season in config["seasons"]:
                            try:
                                if sport_key in ["NFL", "NBA", "NHL"]:
                                    result = await calculator.calculate_season_trends(
                                        season=season, season_type=config["season_type"], weeks=config["weeks"]
                                    )
                                else:
                                    result = await calculator.calculate_season_trends(
                                        season=season,
                                        season_type=config["season_type"],
                                        start_date=config.get("start_date"),
                                        end_date=config.get("end_date"),
                                    )

                                games_processed = result.get("games_processed", 0)
                                teams = result.get("teams", [])
                                total_games += games_processed
                                total_teams.update(teams)

                                results[f"{sport_key}_{season}"] = {
                                    "games_processed": games_processed,
                                    "teams_updated": result.get("teams_updated", 0),
                                }
                                print(
                                    f"[BACKFILL] ✓ {sport_key} {season}: {games_processed} games, {result.get('teams_updated', 0)} teams"
                                )
                            except Exception as season_error:
                                print(f"[BACKFILL] ✗ Error processing {sport_key} {season}: {season_error}")
                                import traceback

                                traceback.print_exc()
                                continue
                    except Exception as sport_error:
                        print(f"[BACKFILL] ✗ Error processing {sport_key}: {sport_error}")
                        import traceback

                        traceback.print_exc()
                        continue

                print(f"[BACKFILL] Complete: {total_games} total games, {len(total_teams)} teams")
                return results

        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_perform_backfill())
            except Exception as e:
                print(f"[BACKFILL] Fatal error in background task: {e}")
                import traceback

                traceback.print_exc()
            finally:
                loop.close()

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

    background_tasks.add_task(_run_backfill)
    elapsed = time.time() - start_time
    return {
        "success": True,
        "message": "Backfill initiated in background for all sports (2024 & 2025)",
        "note": "Check backend console for detailed progress. Existing data will be skipped.",
        "elapsed_seconds": round(elapsed, 2),
    }


