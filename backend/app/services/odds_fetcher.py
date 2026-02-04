"""The Odds API fetcher service"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import not_, select
from sqlalchemy.orm import selectinload
import asyncio
import time

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
    
    # In-memory cache for game lists (1 minute TTL)
    _games_cache: Dict[str, Tuple[List, float]] = {}
    _cache_ttl_seconds = 60
    
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

    @staticmethod
    def _has_usable_h2h_odds(game: Game) -> bool:
        """
        Return True if the ORM `Game` has a usable H2H (moneyline) market.

        “Usable” means: at least one `h2h` market with >=2 odds rows that have a price/implied_prob.

        This prevents us from treating ESPN schedule-only rows (markets empty) as a valid cache hit,
        which would otherwise cause the UI to fall back to 50/50 win probs.
        """
        markets = getattr(game, "markets", None) or []
        for market in markets:
            market_type = str(getattr(market, "market_type", "") or "").lower()
            if market_type != "h2h":
                continue

            odds_rows = getattr(market, "odds", None) or []
            valid = 0
            for odd in odds_rows:
                price = getattr(odd, "price", None)
                implied_prob = getattr(odd, "implied_prob", None)
                if price is not None and str(price).strip():
                    valid += 1
                elif implied_prob is not None:
                    valid += 1
                if valid >= 2:
                    return True
        return False

    async def normalize_and_store_odds(
        self, api_data: List[dict], sport_config: SportConfig
    ) -> List[Game]:
        """
        Persist Odds API payload into games/markets/odds tables.
        Used by OddsSyncWorker and admin/scraper routes.
        """
        return await self._data_store.normalize_and_store_odds(api_data, sport_config)

    async def fetch_odds_for_sport(
        self,
        sport_config: SportConfig,
        markets: Optional[List[str]] = None,
        force_refresh: bool = False,
        include_premium_markets: bool = False,
    ) -> List[dict]:
        """
        Fetch odds for a specific sport from The Odds API with rate limiting.
        
        Uses rate limiter to:
        - Deduplicate concurrent requests
        - Enforce minimum time between calls
        - Track quota usage
        
        Args:
            sport_config: Sport configuration
            markets: Optional list of markets to fetch (overrides default)
            force_refresh: Whether to bypass local cache (still respects rate limits)
            include_premium_markets: If True, includes premium markets (e.g., player_props) in request
        """
        rate_limiter = get_rate_limiter()
        sport_key = sport_config.odds_key

        # Build markets list: use provided markets, or default, and optionally add premium markets
        if markets is not None:
            markets_list = list(markets)
        else:
            markets_list = list(sport_config.default_markets)
        
        # Add premium markets if requested and available
        if include_premium_markets and sport_config.premium_markets:
            for premium_market in sport_config.premium_markets:
                if premium_market not in markets_list:
                    markets_list.append(premium_market)
        
        requested_markets = ",".join(markets_list)

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
                msg = (
                    f"Rate limit: Please wait {int(time_until)} more seconds before refreshing {sport_config.display_name} games. "
                    f"API calls are limited to once every 5 minutes per sport to preserve quota."
                )
                try:
                    from app.services.alerting import get_alerting_service
                    await get_alerting_service().emit(
                        "odds.fetch.fail",
                        "warning",
                        {"reason": "rate_limit", "message": msg[:200], "sport_key": sport_key},
                        sport=sport_key,
                    )
                except Exception:
                    pass
                raise Exception(msg)
        
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
        force_refresh: bool = False,
        include_premium_markets: bool = False,
    ) -> List[GameResponse]:
        import time
        
        # Check in-memory cache first (unless force refresh)
        cache_key = f"{sport_identifier}:{include_premium_markets}"
        if not force_refresh and cache_key in self._games_cache:
            cached_data, cached_time = self._games_cache[cache_key]
            if (time.time() - cached_time) < self._cache_ttl_seconds:
                print(f"[ODDS_FETCHER] Using cached games list (age: {time.time() - cached_time:.1f}s)")
                return cached_data
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
                # First, try to fix existing games with placeholder team names
                await self._fix_placeholder_team_names(sport_config, cutoff_time, future_cutoff)
                
                # Use selectinload for efficient relationship loading (avoids N+1 queries)
                # Exclude finished/closed games - only show scheduled or in-progress games
                # Also exclude games with placeholder team names (common during postseason)
                placeholder_names = {"TBD", "TBA", "TBC", "AFC", "NFC", "TO BE DETERMINED", "TO BE ANNOUNCED"}
                result = await self.db.execute(
                    select(Game)
                    .where(Game.sport == sport_config.code)
                    .where(Game.start_time >= cutoff_time)
                    .where(Game.start_time <= future_cutoff)
                    .where(
                        (Game.status.is_(None)) |  # No status (scheduled)
                        (Game.status.notin_(["finished", "closed", "complete", "Final"]))  # Not completed
                    )
                    .where(Game.home_team.notin_(placeholder_names))
                    .where(Game.away_team.notin_(placeholder_names))
                    .where(~Game.home_team.ilike("tbd"))
                    .where(~Game.away_team.ilike("tbd"))
                    .where(~Game.home_team.ilike("afc"))
                    .where(~Game.away_team.ilike("afc"))
                    .where(~Game.home_team.ilike("nfc"))
                    .where(~Game.away_team.ilike("nfc"))
                    .options(selectinload(Game.markets).selectinload(Market.odds))
                    .order_by(Game.start_time)
                    .limit(sport_config.max_full_games)
                )
                games = self._deduper.dedupe(result.scalars().all())
                db_elapsed = time.time() - db_start
                print(f"[ODDS_FETCHER] Database query took {db_elapsed:.2f}s, found {len(games)} games")
                
                # If we have games, return them immediately (even if slightly stale)
                if games:
                    # Completeness gate: if none of the games has usable H2H odds, these are
                    # schedule-only rows (usually from ESPN fallback). Do NOT treat as a cache hit;
                    # fall through to the API fetch path which is rate-limited + distributed-cached.
                    usable_h2h_count = sum(1 for g in games if self._has_usable_h2h_odds(g))
                    ratio = usable_h2h_count / max(1, len(games))
                    print(
                        f"[ODDS_FETCHER] games_cache_completeness_ratio sport={sport_identifier} "
                        f"ratio={ratio:.2f} count={usable_h2h_count}/{len(games)}"
                    )
                    if usable_h2h_count == 0 or ratio < 0.30:
                        print(
                            f"[ODDS_FETCHER] Cached games incomplete for {sport_config.display_name}: "
                            f"{usable_h2h_count}/{len(games)} have usable h2h odds (ratio={ratio:.2f}); "
                            f"falling through to odds fetch"
                        )
                    else:
                        convert_start = time.time()
                        response = self._converter.to_response(games)
                        convert_elapsed = time.time() - convert_start
                        total_elapsed = time.time() - start_time
                        print(f"[ODDS_FETCHER] Conversion took {convert_elapsed:.2f}s, total: {total_elapsed:.2f}s")
                        # Cache the response
                        cache_key = f"{sport_identifier}:{include_premium_markets}"
                        self._games_cache[cache_key] = (response, time.time())
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
            api_data = await self.fetch_odds_for_sport(
                sport_config, 
                force_refresh=force_refresh,
                include_premium_markets=include_premium_markets
            )
            api_elapsed = time.time() - api_start
            print(f"[ODDS_FETCHER] API call took {api_elapsed:.2f}s, got {len(api_data)} games")
            
            store_start = time.time()
            games = await self._data_store.normalize_and_store_odds(api_data, sport_config)
            store_elapsed = time.time() - store_start
            print(f"[ODDS_FETCHER] Storing took {store_elapsed:.2f}s")
            
            # For NFL, if we got games but they're all placeholders (postseason issue), try ESPN fallback
            if sport_config.code == "NFL" and games:
                placeholder_names = {"TBD", "TBA", "TBC", "AFC", "NFC", "TO BE DETERMINED", "TO BE ANNOUNCED"}
                valid_games = [
                    g for g in games 
                    if g.home_team.upper() not in placeholder_names 
                    and g.away_team.upper() not in placeholder_names
                ]
                if not valid_games:
                    print(f"[ODDS_FETCHER] All {len(games)} NFL games from Odds API have placeholder team names (TBD/AFC/NFC), trying ESPN fallback...")
                    try:
                        from app.services.espn_schedule_games_service import EspnScheduleGamesService
                        espn_service = EspnScheduleGamesService(self.db)
                        await espn_service.ensure_upcoming_games(sport_config=sport_config)
                        
                        # Try to update placeholder team names in existing games with ESPN data.
                        # ESPN schedule has real team names (e.g. Super Bowl); we match by time and copy names.
                        placeholder_names = {"TBD", "TBA", "TBC", "AFC", "NFC", "TO BE DETERMINED", "TO BE ANNOUNCED"}
                        updated_any = False
                        for game in games:
                            if (game.home_team.upper() in placeholder_names or
                                game.away_team.upper() in placeholder_names):
                                # Find matching game with real team names (ESPN row we just inserted)
                                time_window_start = game.start_time - timedelta(hours=6)
                                time_window_end = game.start_time + timedelta(hours=6)
                                espn_result = await self.db.execute(
                                    select(Game)
                                    .where(Game.sport == sport_config.code)
                                    .where(Game.start_time >= time_window_start)
                                    .where(Game.start_time <= time_window_end)
                                    .where(not_(Game.home_team.in_(placeholder_names)))
                                    .where(not_(Game.away_team.in_(placeholder_names)))
                                    .where(Game.id != game.id)
                                    .order_by(Game.start_time)
                                    .limit(1)
                                )
                                espn_game = espn_result.scalar_one_or_none()
                                if espn_game:
                                    game.home_team = espn_game.home_team
                                    game.away_team = espn_game.away_team
                                    updated_any = True
                                    print(
                                        f"[ODDS_FETCHER] Updated game {game.id} team names from ESPN: "
                                        f"{espn_game.away_team} @ {espn_game.home_team}"
                                    )
                        if updated_any:
                            await self.db.commit()
                            # Return the Odds API games (with markets) that now have correct team names
                            print(f"[ODDS_FETCHER] Placeholder team names fixed; returning games with odds")
                            # Fall through to normal path so we return games with markets
                        else:
                            await self.db.commit()
                            schedule_response = await espn_service.get_upcoming_games_response(sport_config=sport_config)
                            if schedule_response:
                                print(
                                    f"[ODDS_FETCHER] No ESPN match for placeholders; "
                                    f"returning {len(schedule_response)} ESPN schedule games"
                                )
                                return schedule_response
                    except Exception as espn_error:
                        print(f"[ODDS_FETCHER] ESPN fallback failed: {espn_error}")
                        import traceback
                        traceback.print_exc()
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

            try:
                from app.services.alerting import get_alerting_service
                await get_alerting_service().emit(
                    "odds.fetch.fail",
                    "warning",
                    {"reason": "all_queries_failed", "sport_identifier": sport_identifier},
                    sport=sport_config.code if sport_config else sport_identifier,
                )
            except Exception:
                pass
            print(f"[ODDS_FETCHER] All queries failed, returning empty array")
            return []
        
        return []
    
    async def _fix_placeholder_team_names(self, sport_config: SportConfig, cutoff_time: datetime, future_cutoff: datetime):
        """
        Fix existing games in database that have placeholder team names (AFC, NFC, TBD, etc.)
        by finding matching ESPN games and updating team names.
        """
        placeholder_names = {"TBD", "TBA", "TBC", "AFC", "NFC", "TO BE DETERMINED", "TO BE ANNOUNCED"}
        
        # Find games with placeholder team names
        placeholder_result = await self.db.execute(
            select(Game)
            .where(Game.sport == sport_config.code)
            .where(Game.start_time >= cutoff_time)
            .where(Game.start_time <= future_cutoff)
            .where(
                (Game.home_team.in_(placeholder_names)) | 
                (Game.away_team.in_(placeholder_names))
            )
        )
        placeholder_games = placeholder_result.scalars().all()
        
        if not placeholder_games:
            return
        
        print(f"[ODDS_FETCHER] Found {len(placeholder_games)} games with placeholder team names, attempting to fix...")
        
        # Ensure ESPN games are loaded
        try:
            from app.services.espn_schedule_games_service import EspnScheduleGamesService
            espn_service = EspnScheduleGamesService(self.db)
            await espn_service.ensure_upcoming_games(sport_config=sport_config)
        except Exception as e:
            print(f"[ODDS_FETCHER] Failed to load ESPN games for fixing placeholders: {e}")
            return
        
        updated_count = 0
        from sqlalchemy import not_
        
        for game in placeholder_games:
            # Try to find matching ESPN game by time window (wider window for post-season)
            time_window_hours = 6 if sport_config.code == "NFL" else 2  # Wider window for NFL post-season
            time_window_start = game.start_time - timedelta(hours=time_window_hours)
            time_window_end = game.start_time + timedelta(hours=time_window_hours)
            
            # Prefer ESPN rows (external_game_id like 'espn:%') for real team names in the same time window
            espn_result = await self.db.execute(
                select(Game)
                .where(Game.sport == sport_config.code)
                .where(Game.start_time >= time_window_start)
                .where(Game.start_time <= time_window_end)
                .where(not_(Game.home_team.in_(placeholder_names)))
                .where(not_(Game.away_team.in_(placeholder_names)))
                .where(Game.id != game.id)
                .where(Game.external_game_id.like("espn:%"))
                .order_by(Game.start_time)
                .limit(10)
            )
            candidates = espn_result.scalars().all()
            if not candidates:
                espn_result = await self.db.execute(
                    select(Game)
                    .where(Game.sport == sport_config.code)
                    .where(Game.start_time >= time_window_start)
                    .where(Game.start_time <= time_window_end)
                    .where(not_(Game.home_team.in_(placeholder_names)))
                    .where(not_(Game.away_team.in_(placeholder_names)))
                    .where(Game.id != game.id)
                    .order_by(Game.start_time)
                    .limit(10)
                )
                candidates = espn_result.scalars().all()
            
            # Find the best match (closest time, has markets if original has markets)
            best_match = None
            min_time_diff = None
            
            for candidate in candidates:
                time_diff = abs((candidate.start_time - game.start_time).total_seconds())
                
                # Prefer games with markets if the original game has markets
                if hasattr(game, 'markets') and game.markets:
                    if hasattr(candidate, 'markets') and candidate.markets:
                        if best_match is None or time_diff < min_time_diff:
                            best_match = candidate
                            min_time_diff = time_diff
                else:
                    # If original has no markets, any candidate is fine, but prefer closest time
                    if best_match is None or time_diff < min_time_diff:
                        best_match = candidate
                        min_time_diff = time_diff
            
            if best_match:
                # Update team names
                old_home = game.home_team
                old_away = game.away_team
                game.home_team = best_match.home_team
                game.away_team = best_match.away_team
                updated_count += 1
                print(f"[ODDS_FETCHER] ✅ Fixed game {game.id}: '{old_away} @ {old_home}' -> '{game.away_team} @ {game.home_team}' (matched by time: {min_time_diff/60:.1f} min diff)")
            else:
                print(f"[ODDS_FETCHER] ⚠️  Could not find match for game {game.id} with placeholders '{game.away_team} @ {game.home_team}' at {game.start_time}")
        
        if updated_count > 0:
            try:
                await self.db.commit()
                print(f"[ODDS_FETCHER] Successfully updated {updated_count} games with placeholder team names")
            except Exception as e:
                await self.db.rollback()
                print(f"[ODDS_FETCHER] Failed to commit team name updates: {e}")

