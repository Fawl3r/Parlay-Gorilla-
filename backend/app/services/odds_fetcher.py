"""The Odds API fetcher service"""

import httpx
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from app.schemas.game import GameResponse
from app.services.sports_config import SportConfig, get_sport_config
from app.utils.nfl_week import calculate_nfl_week


class OddsFetcherService:
    """Service for fetching and storing odds from The Odds API"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_key = settings.the_odds_api_key
    
    def _american_to_decimal(self, american_odds: int) -> Decimal:
        """Convert American odds to decimal odds"""
        if american_odds > 0:
            return Decimal(american_odds) / Decimal(100) + Decimal(1)
        else:
            return Decimal(100) / Decimal(abs(american_odds)) + Decimal(1)
    
    def _decimal_to_implied_prob(self, decimal_odds: Decimal) -> Decimal:
        """Convert decimal odds to implied probability"""
        return Decimal(1) / decimal_odds
    
    async def fetch_odds_for_sport(
        self,
        sport_config: SportConfig,
        markets: Optional[List[str]] = None,
    ) -> List[dict]:
        """Fetch odds for a specific sport from The Odds API"""
        requested_markets = ",".join(markets or sport_config.default_markets)
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/sports/{sport_config.odds_key}/odds",
                    params={
                        "apiKey": self.api_key,
                        "regions": "us",
                        "markets": requested_markets,
                        "oddsFormat": "american",
                    },
                    follow_redirects=True,
                )
                response.raise_for_status()
                data = response.json()
                
                # Validate we got data
                if not isinstance(data, list):
                    raise Exception("Invalid response format from The Odds API")
                
                return data
            except httpx.TimeoutException:
                raise Exception("The Odds API request timed out. Please try again later.")
            except httpx.HTTPStatusError as e:
                error_msg = f"The Odds API returned error {e.response.status_code}"
                try:
                    error_detail = e.response.json()
                    error_msg += f": {error_detail}"
                except:
                    error_msg += f": {e.response.text[:200]}"
                raise Exception(error_msg)
            except httpx.HTTPError as e:
                raise Exception(f"Failed to fetch odds from The Odds API: {str(e)}")
    
    async def normalize_and_store_odds(
        self,
        api_data: List[dict],
        sport_config: SportConfig,
    ) -> List[Game]:
        """Normalize API data and store in database (optimized)"""
        if not api_data:
            return []
        
        # Batch fetch existing games
        external_ids = [event.get("id") for event in api_data if event.get("id")]
        existing_games_result = await self.db.execute(
            select(Game).where(
                Game.external_game_id.in_(external_ids),
                Game.sport == sport_config.code,
            )
        )
        existing_games = {game.external_game_id: game for game in existing_games_result.scalars().all()}
        
        games = []
        new_games = []
        
        for event in api_data:
            external_game_id = event.get("id")
            if not external_game_id:
                continue
                
            home_team = event.get("home_team", "")
            away_team = event.get("away_team", "")
            
            try:
                commence_time = datetime.fromisoformat(event.get("commence_time", "").replace("Z", "+00:00"))
            except:
                continue  # Skip invalid dates
            
            # Get or create game
            game = existing_games.get(external_game_id)
            if not game:
                game = Game(
                    external_game_id=external_game_id,
                    sport=sport_config.code,
                    home_team=home_team,
                    away_team=away_team,
                    start_time=commence_time,
                    status="scheduled",
                )
                new_games.append(game)
                self.db.add(game)
                await self.db.flush()  # Flush to get the game ID
                existing_games[external_game_id] = game  # Add to dict for later use
            
            # Process bookmakers (limit to first 3 books for speed)
            bookmakers = event.get("bookmakers", [])[:3]
            for bookmaker in bookmakers:
                book_name = bookmaker.get("key", "").lower()
                markets_data = bookmaker.get("markets", [])
                
                for market_data in markets_data:
                    market_type = market_data.get("key", "")
                    if market_type not in sport_config.supported_markets:
                        continue  # Skip unsupported markets
                    
                    outcomes = market_data.get("outcomes", [])
                    
                    # Find or create market (batch check later if needed)
                    result = await self.db.execute(
                        select(Market).where(
                            Market.game_id == game.id,
                            Market.market_type == market_type,
                            Market.book == book_name,
                        ).limit(1)
                    )
                    market = result.scalar_one_or_none()
                    
                    if not market:
                        market = Market(
                            game_id=game.id,
                            market_type=market_type,
                            book=book_name,
                        )
                        self.db.add(market)
                        await self.db.flush()  # Need ID for odds
                    
                    # Process outcomes (limit to avoid too many odds)
                    for outcome_data in outcomes[:10]:  # Limit outcomes per market
                        outcome_name = outcome_data.get("name", "")
                        price_american = outcome_data.get("price", 0)
                        
                        if not price_american:
                            continue
                        
                        # Convert to decimal and implied probability
                        decimal_price = self._american_to_decimal(price_american)
                        implied_prob = self._decimal_to_implied_prob(decimal_price)
                        
                        # Normalize outcome name
                        if market_type == "h2h":
                            outcome = "home" if outcome_name == home_team else "away"
                        elif market_type == "spreads":
                            point = outcome_data.get("point", 0)
                            outcome = f"{outcome_name} {point:+.1f}"
                        elif market_type == "totals":
                            point = outcome_data.get("point", 0)
                            outcome = f"{outcome_name} {point:.1f}"
                        else:
                            outcome = outcome_name
                        
                        # Check if odds already exist to avoid duplicates
                        result = await self.db.execute(
                            select(Odds).where(
                                Odds.market_id == market.id,
                                Odds.outcome == outcome,
                            ).limit(1)
                        )
                        existing_odds = result.scalar_one_or_none()
                        
                        if not existing_odds:
                            odds = Odds(
                                market_id=market.id,
                                outcome=outcome,
                                price=f"+{price_american}" if price_american > 0 else str(price_american),
                                decimal_price=decimal_price,
                                implied_prob=implied_prob,
                            )
                            self.db.add(odds)
            
            games.append(game)
        
        # Commit all at once
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            print(f"Error committing games: {e}")
            # Return what we have
            return games
        
        return games
    
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
        
        # First, try to get cached games quickly
        if not force_refresh:
            print(f"[ODDS_FETCHER] Checking database for cached games...")
            db_start = time.time()
            try:
                # Use selectinload for efficient relationship loading (avoids N+1 queries)
                result = await self.db.execute(
                    select(Game)
                    .where(Game.sport == sport_config.code)
                    .where(Game.start_time >= cutoff_time)
                    .where(Game.start_time <= future_cutoff)
                    .options(selectinload(Game.markets).selectinload(Market.odds))
                    .order_by(Game.start_time)
                    .limit(sport_config.max_full_games)
                )
                games = result.scalars().all()
                db_elapsed = time.time() - db_start
                print(f"[ODDS_FETCHER] Database query took {db_elapsed:.2f}s, found {len(games)} games")
                
                # If we have games, return them immediately (even if slightly stale)
                if games:
                    convert_start = time.time()
                    response = self._convert_games_to_response(games)
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
            api_data = await self.fetch_odds_for_sport(sport_config)
            api_elapsed = time.time() - api_start
            print(f"[ODDS_FETCHER] API call took {api_elapsed:.2f}s, got {len(api_data)} games")
            
            store_start = time.time()
            games = await self.normalize_and_store_odds(api_data, sport_config)
            store_elapsed = time.time() - store_start
            print(f"[ODDS_FETCHER] Storing took {store_elapsed:.2f}s")
            
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
                response = self._convert_games_to_response(games)
                convert_elapsed = time.time() - convert_start
                total_elapsed = time.time() - start_time
                print(f"[ODDS_FETCHER] Total time: {total_elapsed:.2f}s (API: {api_elapsed:.2f}s, Store: {store_elapsed:.2f}s, Load Relations: {reload_elapsed:.2f}s, Convert: {convert_elapsed:.2f}s)")
                return response
        except Exception as e:
            # If API fetch fails, try to return stale data
            print(f"[ODDS_FETCHER] Error fetching from API: {e}")
            import traceback
            traceback.print_exc()
            
            try:
                # Use a more lenient date range for fallback
                fallback_cutoff = datetime.utcnow() - timedelta(days=14)
                # Try with relationships first
                try:
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
                        print(f"[ODDS_FETCHER] Returning {len(games)} stale games as fallback")
                        return self._convert_games_to_response(games)
                except Exception as relationship_error:
                    # If relationships fail, try without them
                    print(f"[ODDS_FETCHER] Relationship loading failed, trying without: {relationship_error}")
                    result = await self.db.execute(
                        select(Game)
                        .where(Game.sport == sport_config.code)
                        .where(Game.start_time >= fallback_cutoff)
                        .order_by(Game.start_time.desc())
                        .limit(sport_config.max_full_games)
                    )
                    games = result.scalars().all()
                    if games:
                        # Return games without markets/odds
                        simple_response = []
                        for game in games:
                            week = calculate_nfl_week(game.start_time) if game.sport == "NFL" else None
                            game_dict = {
                                "id": str(game.id),
                                "external_game_id": game.external_game_id,
                                "sport": game.sport,
                                "home_team": game.home_team,
                                "away_team": game.away_team,
                                "start_time": game.start_time,
                                "status": game.status,
                                "week": week,
                                "markets": [],  # Empty markets
                            }
                            simple_response.append(GameResponse.model_validate(game_dict))
                        print(f"[ODDS_FETCHER] Returning {len(simple_response)} games without odds as fallback")
                        return simple_response
            except Exception as fallback_error:
                print(f"[ODDS_FETCHER] Fallback query also failed: {fallback_error}")
                import traceback
                traceback.print_exc()
            
            # Return empty array instead of raising to prevent 500 error
            print(f"[ODDS_FETCHER] All queries failed, returning empty array")
            return []
        
        return []
    
    def _convert_games_to_response(self, games: List[Game]) -> List[GameResponse]:
        """Convert Game objects to GameResponse schemas"""
        result = []
        for game in games:
            # Calculate NFL week if sport is NFL
            week = None
            if game.sport == "NFL":
                week = calculate_nfl_week(game.start_time)
            
            game_dict = {
                "id": str(game.id),
                "external_game_id": game.external_game_id,
                "sport": game.sport,
                "home_team": game.home_team,
                "away_team": game.away_team,
                "start_time": game.start_time,
                "status": game.status,
                "week": week,
                "markets": [
                    {
                        "id": str(market.id),
                        "market_type": market.market_type,
                        "book": market.book,
                        "odds": [
                            {
                                "id": str(odd.id),
                                "outcome": odd.outcome,
                                "price": odd.price,
                                "decimal_price": float(odd.decimal_price),
                                "implied_prob": float(odd.implied_prob),
                                "created_at": odd.created_at.isoformat() if odd.created_at else None,
                            }
                            for odd in market.odds
                        ],
                    }
                    for market in game.markets
                ],
            }
            result.append(GameResponse.model_validate(game_dict))
        return result

