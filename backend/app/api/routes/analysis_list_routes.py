"""Analysis list + cache endpoints.

Separated from `analysis.py` to keep route modules small and focused.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.schemas.analysis import GameAnalysisListItem
from app.services.alerting.alerting_service import get_alerting_service
from app.services.sports_config import get_sport_config
from app.utils.placeholders import is_placeholder_team
from app.utils.timezone_utils import TimezoneNormalizer

router = APIRouter()

# Simple cache for analysis list (5 minutes)
_analysis_list_cache: Dict[str, tuple] = {}  # key -> (data, timestamp)
ANALYSIS_CACHE_TTL = 300  # 5 minutes


@router.post("/analysis/cache/clear", summary="Clear analysis list cache")
async def clear_analysis_cache():
    """Clear the in-memory analysis list cache."""
    global _analysis_list_cache
    cache_size = len(_analysis_list_cache)
    _analysis_list_cache.clear()
    print(f"[Analysis API] Cleared analysis cache ({cache_size} entries)")
    return {
        "success": True,
        "message": f"Analysis cache cleared ({cache_size} entries removed)",
        "cache_size_before": cache_size,
    }


# NOTE: This route MUST come before /{slug:path} to avoid being captured by the path parameter
@router.get("/analysis/{sport}/upcoming", response_model=List[GameAnalysisListItem])
async def list_upcoming_analyses(
    sport: str,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List available analyses for upcoming games - optimized with caching."""
    import asyncio
    import time

    start_time = time.time()

    # Check cache first
    cache_key = f"{sport}:{limit}"
    if cache_key in _analysis_list_cache:
        cached_data, cached_time = _analysis_list_cache[cache_key]
        cache_age = (datetime.utcnow() - cached_time).total_seconds()
        if cache_age < ANALYSIS_CACHE_TTL:
            elapsed = time.time() - start_time
            print(
                f"[Analysis API] Returning cached data (age: {cache_age:.0f}s) in {elapsed:.3f}s"
            )
            return cached_data

    # Wrap the entire operation in a timeout to prevent hanging
    try:
        return await asyncio.wait_for(
            _fetch_analyses_list(sport, limit, db, cache_key),
            timeout=25.0,  # less than frontend's 30s
        )
    except asyncio.TimeoutError:
        print(f"[Analysis API] TIMEOUT: Request took longer than 25s for {sport}")
        # Return cached data if available, even if stale
        if cache_key in _analysis_list_cache:
            cached_data, _ = _analysis_list_cache[cache_key]
            print("[Analysis API] Returning stale cached data due to timeout")
            return cached_data
        return []
    except Exception as e:
        print(f"[Analysis API] Error in list_upcoming_analyses: {e}")
        import traceback

        traceback.print_exc()
        return []


async def _fetch_analyses_list(
    sport: str,
    limit: int,
    db: AsyncSession,
    cache_key: str,
) -> List[GameAnalysisListItem]:
    """Internal function to fetch analyses list."""
    import time

    start_time = time.time()

    try:
        sport_config = get_sport_config(sport)
        league = sport_config.code

        now = datetime.utcnow()
        # Keep the analysis list aligned with the games endpoint:
        # include recently started games to avoid an "empty" UI after the first kickoff.
        cutoff_time = now - timedelta(hours=24)
        future_cutoff = now + timedelta(days=sport_config.lookahead_days)

        async def _query_rows():
            query_start = time.time()
            result = await db.execute(
                # Always list (recent + upcoming) games; attach analysis metadata when available.
                #
                # This avoids the "empty list" problem in dev/local environments where
                # analyses might not be pre-generated yet (scheduler runs at 6AM).
                select(Game, GameAnalysis)
                .outerjoin(
                    GameAnalysis,
                    (GameAnalysis.game_id == Game.id) & (GameAnalysis.league == league),
                )
                .where(
                    Game.sport == league,
                    Game.start_time >= cutoff_time,
                    Game.start_time <= future_cutoff,
                    # Exclude finished/closed games - only show scheduled or in-progress games
                    (Game.status.is_(None)) |  # No status (scheduled)
                    (Game.status.notin_(["finished", "closed", "complete", "Final"]))  # Not completed
                )
                .order_by(Game.start_time)
                .limit(limit)
            )
            query_elapsed = time.time() - query_start
            if query_elapsed > 1.0:
                print(f"[Analysis API] Slow query: {query_elapsed:.2f}s for {sport}")
            fetch_start = time.time()
            rows = result.all()
            fetch_elapsed = time.time() - fetch_start
            if fetch_elapsed > 1.0:
                print(f"[Analysis API] Slow fetch: {fetch_elapsed:.2f}s for {sport}")
            return rows, query_elapsed, fetch_elapsed

        try:
            rows, query_elapsed, fetch_elapsed = await _query_rows()

            # If there are no games in the DB window yet, warm the DB from The Odds API
            # (rate-limited + cached) and retry once. This makes /analysis usable even
            # before any other page has loaded games.
            if not rows:
                try:
                    from app.services.odds_fetcher import OddsFetcherService  # local import to avoid import cycles

                    fetcher = OddsFetcherService(db)
                    await fetcher.get_or_fetch_games(sport_config.slug, force_refresh=False)
                except Exception as warm_error:
                    print(f"[Analysis API] Warm games failed for {sport}: {warm_error}")

                rows, query_elapsed, fetch_elapsed = await _query_rows()

            process_start = time.time()
            items: List[GameAnalysisListItem] = []
            placeholder_slugs: List[str] = []

            from app.api.routes.analysis import _generate_slug  # runtime import to avoid cycles
            fallback_generated_at = TimezoneNormalizer.ensure_utc(datetime.utcnow())

            for game, analysis in rows:
                try:
                    slug = (
                        str(getattr(analysis, "slug", "") or "").strip()
                        if analysis is not None
                        else _generate_slug(
                            home_team=game.home_team,
                            away_team=game.away_team,
                            league=game.sport,
                            game_time=game.start_time,
                        )
                    )
                    if is_placeholder_team(game.home_team) or is_placeholder_team(game.away_team):
                        placeholder_slugs.append(slug or f"{game.away_team} @ {game.home_team}")
                    items.append(
                        GameAnalysisListItem(
                            id=str(analysis.id) if analysis is not None else str(game.id),
                            slug=slug,
                            league=str(analysis.league) if analysis is not None else league,
                            matchup=str(analysis.matchup) if analysis is not None else f"{game.away_team} @ {game.home_team}",
                            game_time=TimezoneNormalizer.ensure_utc(game.start_time),
                            generated_at=TimezoneNormalizer.ensure_utc(analysis.generated_at) if analysis is not None else fallback_generated_at,
                        )
                    )
                except Exception as item_error:
                    print(
                        f"[Analysis API] Error processing list item for game {getattr(game, 'id', 'unknown')}: {item_error}"
                    )
                    continue

            # Alert when analysis list is served with any games showing placeholder team names
            if placeholder_slugs:
                try:
                    alerting = get_alerting_service()
                    await alerting.emit(
                        "analysis.list.teams.placeholder",
                        "warning",
                        {
                            "count": len(placeholder_slugs),
                            "sample_slugs": placeholder_slugs[:5],
                        },
                        sport=league,
                        next_action_hint="Run schedule repair or backfill; check API-Sports/ESPN.",
                    )
                except Exception as alert_err:
                    print(f"[Analysis API] Alert emit failed: {alert_err}")

            process_elapsed = time.time() - process_start
            total_elapsed = time.time() - start_time
            if total_elapsed > 2.0:
                print(
                    "[Analysis API] Slow endpoint: "
                    f"{total_elapsed:.2f}s total (query: {query_elapsed:.2f}s, "
                    f"fetch: {fetch_elapsed:.2f}s, process: {process_elapsed:.2f}s)"
                )

            _analysis_list_cache[cache_key] = (items, datetime.utcnow())
            return items
        except Exception as db_error:
            print(f"[Analysis API] Database query error: {db_error}")
            try:
                result = await db.execute(
                    select(GameAnalysis)
                    .where(GameAnalysis.league == league, GameAnalysis.expires_at >= now)
                    .order_by(GameAnalysis.generated_at.desc())
                    .limit(limit)
                )

                items: List[GameAnalysisListItem] = []
                for analysis in result.scalars().all():
                    items.append(
                        GameAnalysisListItem(
                            id=str(analysis.id),
                            slug=analysis.slug,
                            league=analysis.league,
                            matchup=analysis.matchup,
                            game_time=TimezoneNormalizer.ensure_utc(
                                analysis.generated_at
                            ),  # fallback
                            generated_at=TimezoneNormalizer.ensure_utc(analysis.generated_at),
                        )
                    )

                _analysis_list_cache[cache_key] = (items, datetime.utcnow())
                return items
            except Exception as fallback_error:
                print(f"[Analysis API] Fallback query also failed: {fallback_error}")
                return []
    except Exception as e:
        print(f"[Analysis API] Error listing analyses: {e}")
        import traceback

        traceback.print_exc()
        return []



