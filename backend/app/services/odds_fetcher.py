"""The Odds API fetcher service"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import asyncio

from app.core.config import settings
from app.models.game import Game
from app.models.market import Market
from app.schemas.game import GameResponse
from app.services.game_response_converter import GameResponseConverter
from app.services.games_deduplication_service import GamesDeduplicationService
from app.services.odds_api.odds_api_data_store import OddsApiDataStore
from app.services.sports_config import SportConfig, get_sport_config
from app.services.odds_api_rate_limiter import get_rate_limiter
from app.services.the_odds_api_client import OddsApiKeys, TheOddsApiClient
from app.services.odds_api.distributed_odds_api_cache import DistributedOddsApiCache


class OddsFetcherService:
    """Service for fetching and storing odds from The Odds API"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._api = TheOddsApiClient(
            api_keys=OddsApiKeys(
                primary=settings.the_odds_api_key,
                fallback=getattr(settings, "the_odds_api_fallback_key", None),
            )
        )
        self._converter = GameResponseConverter()
        self._deduper = GamesDeduplicationService()
        self._data_store = OddsApiDataStore(db)
    
    async def fetch_odds_for_sport(
        self,
        sport_config: SportConfig,
        markets: Optional[List[str]] = None,
        force_refresh: bool = False,
    ) -> List[dict]:
        """
        Fetch odds for a specific sport from The Odds API with rate limiting.
        
        Uses rate limiter to:
        - Deduplicate concurrent requests
        - Enforce minimum time between calls
        - Track quota usage
        """
        rate_limiter = get_rate_limiter()
        sport_key = sport_config.odds_key

        requested_markets = ",".join(markets or sport_config.default_markets)

        # ------------------------------------------------------------------
        # Cluster-wide cache (Redis): this is the primary protection against
        # credit drain in production and during dev reloads.
        #
        # IMPORTANT: `force_refresh` does NOT bypass the distributed cache TTL.
        # Refresh is treated as “bypass local/UI caches”, not “burn credits”.
        # ------------------------------------------------------------------
        distributed_cache = DistributedOddsApiCache()
        if distributed_cache.is_available():
            cache_key = distributed_cache.build_cache_key(
                sport_key=sport_config.odds_key,
                regions="us",
                markets=requested_markets,
                odds_format="american",
            )

            async def _fetch_from_odds_api():
                data = await self._api.get_current_odds(
                    sport_key=sport_config.odds_key,
                    regions="us",
                    markets=requested_markets,
                    odds_format="american",
                    timeout_seconds=15.0,
                )
                if not isinstance(data, list):
                    raise Exception("Invalid response format from The Odds API")
                return data

            try:
                data = await distributed_cache.get_or_fetch(cache_key=cache_key, fetch=_fetch_from_odds_api)
                # Warm local cache too (best-effort; helps if Redis blips).
                try:
                    rate_limiter.cache_response(sport_key, data)
                except Exception:
                    pass
                return data
            except Exception as exc:
                # Fail open: fall back to in-process caching/rate limiting.
                print(f"[ODDS_FETCHER] Redis cache unavailable, falling back to in-process limiter: {exc}")
        
        # Check in-process cache (note: `force_refresh` does NOT bypass, to preserve credits).
        cached = rate_limiter.get_cached_response(sport_key)
        if cached is not None:
            print(f"[ODDS_FETCHER] Using cached response for {sport_config.display_name}")
            return cached
        
        # Check if we should make the API call.
        #
        # IMPORTANT: even when the caller requests a "refresh", we still respect the
        # min call interval to conserve credits. Refresh bypasses local caches, but
        # does not bypass rate limiting.
        should_call = await rate_limiter.acquire(sport_key, force=False)
        
        if not should_call:
            # Check if there's an in-flight request we can wait for
            async with rate_limiter._in_flight_lock:
                if sport_key in rate_limiter._in_flight:
                    task = rate_limiter._in_flight[sport_key]
                    if not task.done():
                        print(f"[ODDS_FETCHER] Waiting for in-flight request for {sport_config.display_name}...")
                        try:
                            # Wait for the existing request to complete (max 30 seconds)
                            result = await asyncio.wait_for(task, timeout=30.0)
                            return result
                        except asyncio.TimeoutError:
                            print(f"[ODDS_FETCHER] Timeout waiting for in-flight request, proceeding with new call")
            
            # Use cached response or return empty
            cached = rate_limiter.get_cached_response(sport_key)
            if cached is not None:
                return cached
            
            # If no cache and rate limited, raise exception
            time_until = rate_limiter.get_time_until_next_call(sport_key)
            if time_until and time_until > 0:
                raise Exception(
                    f"Rate limit: Please wait {int(time_until)} more seconds before refreshing {sport_config.display_name} games. "
                    f"API calls are limited to once every 5 minutes per sport to preserve quota."
                )
        
        # Make the API call
        async def _make_api_call():
            data = await self._api.get_current_odds(
                sport_key=sport_config.odds_key,
                regions="us",
                markets=requested_markets,
                odds_format="american",
                timeout_seconds=15.0,
            )
            if not isinstance(data, list):
                raise Exception("Invalid response format from The Odds API")

            # NOTE: we no longer have direct access to per-response headers here because
            # TheOddsApiClient abstracts key fallback. Usage tracking is handled by
            # The Odds API account console; we conserve credits primarily via caching
            # and min-interval rate limiting.
            rate_limiter.record_call(sport_key, None)
            rate_limiter.cache_response(sport_key, data)
            return data
        
        # Register and execute the request
        task = asyncio.create_task(_make_api_call())
        await rate_limiter.register_request(sport_key, task)
        
        return await task
    
    async def get_or_fetch_games(
        self,
        sport_identifier: str,
        force_refresh: bool = False
    ) -> List[GameResponse]:
        """Get games for a sport from database or fetch from API if needed"""
        import time
        start_time = time.time()
        sport_config = get_sport_config(sport_identifier)
        
        # Check if we have recent games (within next 7 days for upcoming games)
        now = datetime.utcnow()
        # Only show games from the past 24 hours (for live/recent games)
        # and upcoming games within lookahead days
        cutoff_time = now - timedelta(hours=24)
        future_cutoff = now + timedelta(days=sport_config.lookahead_days)
        
        # First, try to get cached games quickly (skip if force_refresh)
        if not force_refresh:
            print(f"[ODDS_FETCHER] Checking database for cached games...")
            db_start = time.time()
            try:
                # Use selectinload for efficient relationship loading (avoids N+1 queries)
                # Exclude finished/closed games - only show scheduled or in-progress games
                # Also exclude games with TBD team names (common during postseason)
                result = await self.db.execute(
                    select(Game)
                    .where(Game.sport == sport_config.code)
                    .where(Game.start_time >= cutoff_time)
                    .where(Game.start_time <= future_cutoff)
                    .where(
                        (Game.status.is_(None)) |  # No status (scheduled)
                        (Game.status.notin_(["finished", "closed", "complete", "Final"]))  # Not completed
                    )
                    .where(Game.home_team != "TBD")
                    .where(Game.away_team != "TBD")
                    .where(~Game.home_team.ilike("tbd"))
                    .where(~Game.away_team.ilike("tbd"))
                    .options(selectinload(Game.markets).selectinload(Market.odds))
                    .order_by(Game.start_time)
                    .limit(sport_config.max_full_games)
                )
                games = self._deduper.dedupe(result.scalars().all())
                db_elapsed = time.time() - db_start
                print(f"[ODDS_FETCHER] Database query took {db_elapsed:.2f}s, found {len(games)} games")
                
                # If we have games, return them immediately (even if slightly stale)
                if games:
                    convert_start = time.time()
                    response = self._converter.to_response(games)
                    convert_elapsed = time.time() - convert_start
                    total_elapsed = time.time() - start_time
                    print(f"[ODDS_FETCHER] Conversion took {convert_elapsed:.2f}s, total: {total_elapsed:.2f}s")
                    return response
            except Exception as db_error:
                print(f"[ODDS_FETCHER] Database query error: {db_error}")
                import traceback
                traceback.print_exc()
                # Continue to API fetch if database query fails
                print(f"[ODDS_FETCHER] Continuing to API fetch due to database error...")
        
        # If no games or force refresh, fetch from API
        print(f"[ODDS_FETCHER] No cached games, fetching from API...")
        try:
            api_start = time.time()
            api_data = await self.fetch_odds_for_sport(sport_config, force_refresh=force_refresh)
            api_elapsed = time.time() - api_start
            print(f"[ODDS_FETCHER] API call took {api_elapsed:.2f}s, got {len(api_data)} games")
            
            store_start = time.time()
            games = await self._data_store.normalize_and_store_odds(api_data, sport_config)
            store_elapsed = time.time() - store_start
            print(f"[ODDS_FETCHER] Storing took {store_elapsed:.2f}s")
            
            # For NFL, if we got games but they're all TBD (postseason issue), try ESPN fallback
            if sport_config.code == "NFL" and games:
                valid_games = [g for g in games if g.home_team.upper() != "TBD" and g.away_team.upper() != "TBD"]
                if not valid_games:
                    print(f"[ODDS_FETCHER] All {len(games)} NFL games from Odds API have TBD teams, trying ESPN fallback...")
                    try:
                        from app.services.espn_schedule_games_service import EspnScheduleGamesService
                        espn_service = EspnScheduleGamesService(self.db)
                        await espn_service.ensure_upcoming_games(sport_config=sport_config)
                        schedule_response = await espn_service.get_upcoming_games_response(sport_config=sport_config)
                        if schedule_response:
                            print(f"[ODDS_FETCHER] ESPN fallback returned {len(schedule_response)} NFL games with actual team names")
                            return schedule_response
                    except Exception as espn_error:
                        print(f"[ODDS_FETCHER] ESPN fallback failed: {espn_error}")
                else:
                    games = valid_games
            
            # Load relationships for the games we just stored (more efficient than reloading)
            if games:
                reload_start = time.time()
                game_ids = [game.id for game in games]
                # Load markets and odds for the games we just created
                result = await self.db.execute(
                    select(Market)
                    .where(Market.game_id.in_(game_ids))
                    .options(selectinload(Market.odds))
                )
                markets = result.scalars().all()
                
                # Attach markets to games (more efficient than reloading all games)
                markets_by_game = {}
                for market in markets:
                    if market.game_id not in markets_by_game:
                        markets_by_game[market.game_id] = []
                    markets_by_game[market.game_id].append(market)
                
                # Attach markets to the games we already have
                for game in games:
                    game.markets = markets_by_game.get(game.id, [])
                
                reload_elapsed = time.time() - reload_start
                print(f"[ODDS_FETCHER] Loading relationships took {reload_elapsed:.2f}s")
                
                convert_start = time.time()
                response = self._converter.to_response(games)
                convert_elapsed = time.time() - convert_start
                total_elapsed = time.time() - start_time
                print(f"[ODDS_FETCHER] Total time: {total_elapsed:.2f}s (API: {api_elapsed:.2f}s, Store: {store_elapsed:.2f}s, Load Relations: {reload_elapsed:.2f}s, Convert: {convert_elapsed:.2f}s)")
                return response
        except Exception as e:
            # If Odds API fetch fails (commonly: OUT_OF_USAGE_CREDITS), fall back to ESPN schedule
            # so the UI can still show upcoming games even without odds.
            print(f"[ODDS_FETCHER] Error fetching from API: {e}")
            import traceback
            traceback.print_exc()

            try:
                from app.services.espn_schedule_games_service import EspnScheduleGamesService

                espn_service = EspnScheduleGamesService(self.db)
                await espn_service.ensure_upcoming_games(sport_config=sport_config)
                schedule_response = await espn_service.get_upcoming_games_response(sport_config=sport_config)
                if schedule_response:
                    print(f"[ODDS_FETCHER] Returning {len(schedule_response)} ESPN schedule games (no odds)")
                    return schedule_response
            except Exception as espn_error:
                print(f"[ODDS_FETCHER] ESPN schedule fallback failed: {espn_error}")

            # Last resort: return any recent DB games (may be stale).
            try:
                fallback_cutoff = datetime.utcnow() - timedelta(days=14)
                result = await self.db.execute(
                    select(Game)
                    .where(Game.sport == sport_config.code)
                    .where(Game.start_time >= fallback_cutoff)
                    .options(selectinload(Game.markets).selectinload(Market.odds))
                    .order_by(Game.start_time.desc())
                    .limit(sport_config.max_full_games)
                )
                games = result.scalars().all()
                if games:
                    print(f"[ODDS_FETCHER] Returning {len(games)} stale games as last resort")
                    return self._converter.to_response(self._deduper.dedupe(games))
            except Exception as fallback_error:
                print(f"[ODDS_FETCHER] Final DB fallback failed: {fallback_error}")

            print(f"[ODDS_FETCHER] All queries failed, returning empty array")
            return []
        
        return []

