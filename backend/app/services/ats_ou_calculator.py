"""
ATS (Against The Spread) and Over/Under Trends Calculator

Calculates ATS and Over/Under trends by:
1. Fetching completed game results from API-Sports (with ESPN fallback)
2. Matching with historical spread/total lines from database
3. Calculating ATS and Over/Under outcomes
4. Aggregating into TeamStats for each team
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.exc import OperationalError
import logging
import re
import asyncio
import httpx

from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from app.models.team_stats import TeamStats
from app.models.game_results import GameResult
from app.services.data_fetchers.espn_scraper import ESPNScraper, get_espn_scraper
from app.repositories.sports_data_repository import SportsDataRepository
from app.services.apisports.results_fetcher import ApiSportsResultsFetcher
from app.services.apisports.data_adapter import ApiSportsDataAdapter
from app.services.apisports.team_mapper import get_team_mapper
from app.core.config import settings

logger = logging.getLogger(__name__)


class ATSOUCalculator:
    """
    Calculate ATS and Over/Under trends from completed games.
    
    Supports NFL, NBA, NHL, MLB, and Soccer (EPL, MLS, etc.).
    Uses API-Sports results (DB-first) with ESPN fallback, combined with
    historical spread/total lines from our database.
    """
    
    # Sport code mappings to API-Sports sport keys and league IDs
    SPORT_MAP = {
        "NFL": ("americanfootball_nfl", 1),  # API-Sports league ID for NFL
        "NBA": ("basketball_nba", 12),
        "NHL": ("icehockey_nhl", 57),
        "MLB": ("baseball_mlb", 1),
        "EPL": ("football", 39),  # English Premier League
        "LALIGA": ("football", 140),  # La Liga
        "MLS": ("football", 253),  # MLS
        "UCL": ("football", 2),  # Champions League
        "SOCCER": ("football", 39),  # Default to EPL
    }
    
    def __init__(self, db: AsyncSession, sport: str = "NFL"):
        self.db = db
        self.sport = sport.upper()
        sport_info = self.SPORT_MAP.get(self.sport)
        if not sport_info:
            raise ValueError(f"Unsupported sport: {sport}. Supported: {list(self.SPORT_MAP.keys())}")
        self.sport_key, self.league_id = sport_info
        
        # API-Sports integration
        self._apisports_repo = SportsDataRepository(db)
        self._results_fetcher = ApiSportsResultsFetcher(db)
        self._data_adapter = ApiSportsDataAdapter()
        self._team_mapper = get_team_mapper()
        
        # Initialize ESPN scraper as fallback
        self.espn = get_espn_scraper()

    async def _commit_with_retry(self, attempts: int = 3) -> None:
        """Commit with retries to handle transient SQLite 'database is locked' errors."""
        for attempt in range(attempts):
            try:
                await self.db.commit()
                return
            except OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < attempts - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"[ATS/OU] Commit blocked by SQLite lock. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                raise

    async def _flush_with_retry(self, attempts: int = 3) -> None:
        """Flush with retries to handle transient SQLite 'database is locked' errors."""
        for attempt in range(attempts):
            try:
                await self.db.flush()
                return
            except OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < attempts - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"[ATS/OU] Flush blocked by SQLite lock. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                raise
    
    async def calculate_season_trends(
        self,
        season: str = "2024",
        season_type: str = "REG",
        weeks: Optional[List[int]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, int]:
        """
        Calculate ATS and Over/Under trends for a season.
        
        Args:
            season: Season year (e.g., "2024" or "2025")
            season_type: "REG", "PRE", or "PST" (NFL/NBA/NHL) or season type for other sports
            weeks: Optional list of weeks to process (NFL/NBA/NHL only, default: all weeks)
            start_date: Optional start date for date-based sports (NBA/NHL/MLB/Soccer)
            end_date: Optional end date for date-based sports (NBA/NHL/MLB/Soccer)
        
        Returns:
            Dict with summary: {"games_processed": X, "teams_updated": Y}
        """
        logger.info(f"[ATS/OU] Starting trend calculation for {self.sport} {season} {season_type} using API-Sports (ESPN fallback)")
        
        # Try API-Sports first (DB-first, no live API calls)
        completed_games = []
        
        if self.sport in ["NFL", "NBA", "NHL"]:
            # Week-based sports: fetch from API-Sports results by date range
            # For week-based, we need to map weeks to dates
            if start_date and end_date:
                completed_games = await self._fetch_completed_games_from_apisports(season, start_date, end_date)
            else:
                # Fallback to ESPN if no date range
                completed_games = await self._fetch_completed_games_espn_fallback(season, season_type, weeks)
        elif self.sport == "MLB":
            if start_date and end_date:
                completed_games = await self._fetch_completed_games_from_apisports(season, start_date, end_date)
            else:
                completed_games = await self._fetch_completed_games_espn_fallback(season, season_type, None)
        elif self.sport in ["EPL", "LALIGA", "MLS", "UCL", "SOCCER"]:
            if start_date and end_date:
                completed_games = await self._fetch_completed_games_from_apisports(season, start_date, end_date)
            else:
                completed_games = await self._fetch_completed_games_espn_fallback(season, season_type, None)
        else:
            logger.error(f"[ATS/OU] Unsupported sport for game fetching: {self.sport}")
            return {"games_processed": 0, "teams_updated": 0, "error": f"Unsupported sport: {self.sport}"}
        
        # If API-Sports returned no games, fallback to ESPN
        if not completed_games:
            logger.info(f"[ATS/OU] No API-Sports results found, falling back to ESPN for {self.sport}")
            if self.sport in ["NFL", "NBA", "NHL"]:
                completed_games = await self._fetch_completed_games_espn_fallback(season, season_type, weeks)
            elif self.sport == "MLB":
                completed_games = await self._fetch_completed_games_espn_fallback(season, season_type, None)
            elif self.sport in ["EPL", "LALIGA", "MLS", "UCL", "SOCCER"]:
                completed_games = await self._fetch_completed_games_espn_fallback(season, season_type, None)
        
        logger.info(f"[ATS/OU] Found {len(completed_games)} completed games")
        
        if not completed_games:
            return {"games_processed": 0, "teams_updated": 0, "error": "No completed games found"}
        
        games_processed = 0
        teams_updated = set()
        
        for game_data in completed_games:
            try:
                # Get or create game result
                game_result = await self._get_or_create_game_result(game_data)
                
                if not game_result:
                    continue
                
                # Get spread and total lines from database
                spread_line, total_line = await self._get_spread_and_total_lines(
                    game_data['home_team'],
                    game_data['away_team'],
                    game_data['game_date'],
                    game_data.get('sport', 'NFL')
                )
                
                # Calculate ATS and Over/Under outcomes
                if game_result.home_score is not None and game_result.away_score is not None:
                    # Calculate ATS
                    if spread_line is not None:
                        ats_outcome = self._calculate_ats(
                            game_result.home_score,
                            game_result.away_score,
                            spread_line
                        )
                        game_result.home_covered_spread = ats_outcome
                        game_result.spread_line = spread_line
                    
                    # Calculate Over/Under
                    if total_line is not None:
                        ou_outcome = self._calculate_over_under(
                            game_result.home_score,
                            game_result.away_score,
                            total_line
                        )
                        game_result.total_over_under = ou_outcome
                        game_result.total_line = total_line
                        game_result.actual_total = game_result.home_score + game_result.away_score
                    
                    await self._commit_with_retry()
                    games_processed += 1
                    if games_processed % 25 == 0:
                        logger.info(
                            f"[ATS/OU] Progress: processed {games_processed} games for {self.sport} {season}"
                        )
                    
                    # Update team stats
                    if game_result.home_score is not None and game_result.away_score is not None:
                        await self._update_team_stats(
                            game_result.home_team,
                            game_result.away_team,
                            game_result,
                            season
                        )
                        teams_updated.add(game_result.home_team)
                        teams_updated.add(game_result.away_team)
                
            except Exception as e:
                logger.error(f"[ATS/OU] Error processing game {game_data.get('id', 'unknown')}: {e}")
                import traceback
                traceback.print_exc()
                await self.db.rollback()
                continue
        
        logger.info(f"[ATS/OU] Processed {games_processed} games, updated {len(teams_updated)} teams")
        return {
            "games_processed": games_processed,
            "teams_updated": len(teams_updated),
            "teams": list(teams_updated)
        }
    
    async def _fetch_completed_games_from_apisports(
        self,
        season: str,
        from_date: date,
        to_date: date
    ) -> List[Dict]:
        """Fetch completed game results from API-Sports results repository (DB-first)."""
        games = []
        
        try:
            # Get results from API-Sports repository (DB-first, no live API calls)
            results = await self._apisports_repo.get_results(
                sport=self.sport_key,
                from_date=datetime.combine(from_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                to_date=datetime.combine(to_date, datetime.max.time()).replace(tzinfo=timezone.utc),
                league_id=self.league_id
            )
            
            if not results:
                logger.info(f"[ATS/OU] No API-Sports results found for {self.sport} from {from_date} to {to_date}")
                return []
            
            # Get existing game results to avoid duplicates
            existing_results = await self._get_existing_game_results(season)
            existing_fixture_ids = {r.external_game_id for r in existing_results if r.external_game_id}
            
            # Convert API-Sports results to internal format
            for result in results:
                if result.fixture_id in existing_fixture_ids:
                    logger.debug(f"[ATS/OU] Skipping fixture {result.fixture_id} - already in database")
                    continue
                
                if result.home_score is not None and result.away_score is not None:
                    # Get team names from team IDs using team mapper (reverse lookup)
                    home_team_name = self._team_mapper.get_team_name(result.home_team_id, self.sport_key) if result.home_team_id else None
                    away_team_name = self._team_mapper.get_team_name(result.away_team_id, self.sport_key) if result.away_team_id else None
                    
                    # If team names not found, try to extract from payload
                    if not home_team_name or not away_team_name:
                        payload = result.payload_json if isinstance(result.payload_json, dict) else {}
                        teams_obj = payload.get("teams", {}) if isinstance(payload.get("teams"), dict) else {}
                        home_team_obj = teams_obj.get("home", {}) if isinstance(teams_obj.get("home"), dict) else {}
                        away_team_obj = teams_obj.get("away", {}) if isinstance(teams_obj.get("away"), dict) else {}
                        home_team_name = home_team_name or home_team_obj.get("name", "")
                        away_team_name = away_team_name or away_team_obj.get("name", "")
                    
                    if home_team_name and away_team_name:
                        games.append({
                            'id': str(result.fixture_id),
                            'home_team': home_team_name,
                            'away_team': away_team_name,
                            'home_score': result.home_score,
                            'away_score': result.away_score,
                            'game_date': result.finished_at or datetime.now(timezone.utc),
                            'sport': self.sport,
                        })
            
            logger.info(f"[ATS/OU] Fetched {len(games)} completed games from API-Sports for {self.sport} from {from_date} to {to_date}")
            
        except Exception as e:
            logger.error(f"[ATS/OU] Error fetching API-Sports results: {e}")
            import traceback
            traceback.print_exc()
        
        return games
    
    async def _fetch_completed_games_by_weeks(
        self,
        season: str,
        season_type: str,
        weeks: Optional[List[int]] = None
    ) -> List[Dict]:
        """Fetch completed games from API-Sports (week-based sports like NFL/NBA/NHL).
        
        For week-based sports, we fetch by date range covering the weeks.
        This is a legacy method name; now uses API-Sports results.
        """
        # Calculate date range for the weeks
        # For now, use a broad date range and filter by weeks if needed
        # In practice, API-Sports results are fetched by date range
        
        season_year = int(season)
        if self.sport == "NFL":
            # NFL season typically runs Sept - Feb
            start_date = date(season_year, 9, 1)
            end_date = date(season_year + 1, 2, 15)
        elif self.sport == "NBA":
            # NBA season typically runs Oct - June
            start_date = date(season_year, 10, 1)
            end_date = date(season_year + 1, 6, 30)
        elif self.sport == "NHL":
            # NHL season typically runs Oct - June
            start_date = date(season_year, 10, 1)
            end_date = date(season_year + 1, 6, 30)
        else:
            # Default: use provided dates or season range
            start_date = date(season_year, 1, 1)
            end_date = date(season_year, 12, 31)
        
        # Fetch from API-Sports
        return await self._fetch_completed_games_from_apisports(season, start_date, end_date)
    
    async def _fetch_completed_games_mlb(
        self,
        season: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """Fetch completed games from API-Sports (MLB - date-based)"""
        # MLB uses date-based schedules
        if not start_date:
            start_date = date(int(season), 3, 1)  # March 1st
        if not end_date:
            end_date = date(int(season), 11, 1)  # November 1st
        
        return await self._fetch_completed_games_from_apisports(season, start_date, end_date)
    
    async def _fetch_completed_games_soccer(
        self,
        season: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """Fetch completed games from API-Sports (Soccer - date-based)"""
        # Soccer uses date-based schedules
        if not start_date:
            start_date = date(int(season), 8, 1)  # August 1st (typical season start)
        if not end_date:
            end_date = date(int(season) + 1, 6, 1)  # June 1st next year
        
        return await self._fetch_completed_games_from_apisports(season, start_date, end_date)
    
    async def _fetch_completed_games_espn_fallback(
        self,
        season: str,
        season_type: str,
        weeks: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Fallback to ESPN scraper when API-Sports has no data.
        Fetches completed games from ESPN by date ranges.
        """
        logger.info(f"[ATS/OU] Using ESPN fallback for {self.sport} {season} {season_type}")
        games = []
        
        try:
            # Map sport to ESPN sport code
            espn_sport_map = {
                "NFL": "nfl",
                "NBA": "nba", 
                "NHL": "nhl",
                "MLB": "mlb",
                "EPL": "soccer_epl",
                "MLS": "soccer_mls"
            }
            
            espn_sport = espn_sport_map.get(self.sport)
            if not espn_sport:
                logger.warning(f"[ATS/OU] No ESPN mapping for sport {self.sport}")
                return []
            
            # Get existing game results to avoid duplicates
            existing_results = await self._get_existing_game_results(season)
            existing_teams_dates = {
                (r.home_team.lower(), r.away_team.lower(), r.game_date.date())
                for r in existing_results
            }
            
            # For NFL, use week-based processing
            if self.sport == "NFL":
                # Calculate week date ranges
                from app.utils.nfl_week import get_week_date_range
                
                # Determine which weeks to process
                weeks_to_process = weeks if weeks else list(range(1, 19))  # Default to weeks 1-18
                
                for week_num in weeks_to_process:
                    try:
                        # Get date range for this week
                        week_start, week_end = get_week_date_range(week_num, int(season))
                        
                        # Fetch games for this date range from ESPN
                        week_games = await self._fetch_espn_games_by_date_range(
                            espn_sport, week_start.date(), week_end.date()
                        )
                        
                        for game in week_games:
                            # Check if we already have this game
                            game_key = (
                                game['home_team'].lower(),
                                game['away_team'].lower(),
                                game['game_date'].date()
                            )
                            if game_key not in existing_teams_dates:
                                game['week'] = week_num
                                games.append(game)
                                existing_teams_dates.add(game_key)  # Prevent duplicates in same batch
                        
                        # Small delay between weeks (ESPN-friendly, faster)
                        await asyncio.sleep(0.25)
                    
                    except Exception as week_error:
                        logger.warning(f"[ATS/OU] Error fetching ESPN data for week {week_num}: {week_error}")
                        continue
            
            # For NBA, NHL, MLB, and Soccer, use date range approach
            elif self.sport in ["NBA", "NHL", "MLB", "EPL", "MLS"]:
                # Use season date ranges
                start_date = date(int(season), 3, 1) if self.sport == "MLB" else date(int(season), 8, 1)
                end_date = date(int(season), 11, 1) if self.sport == "MLB" else date(int(season) + 1, 6, 1)
                
                # Fetch in monthly chunks to avoid overwhelming ESPN
                current_date = start_date
                while current_date <= end_date:
                    # Calculate month end, handling year rollover
                    if current_date.month == 12:
                        next_month_start = date(current_date.year + 1, 1, 1)
                    else:
                        next_month_start = date(current_date.year, current_date.month + 1, 1)
                    month_end = min(
                        next_month_start - timedelta(days=1),
                        end_date
                    )
                    
                    month_games = await self._fetch_espn_games_by_date_range(
                        espn_sport, current_date, month_end
                    )
                    
                    for game in month_games:
                        game_key = (
                            game['home_team'].lower(),
                            game['away_team'].lower(),
                            game['game_date'].date()
                        )
                        if game_key not in existing_teams_dates:
                            games.append(game)
                            existing_teams_dates.add(game_key)
                    
                    # Move to next month
                    if current_date.month == 12:
                        current_date = date(current_date.year + 1, 1, 1)
                    else:
                        current_date = date(current_date.year, current_date.month + 1, 1)
                    
                    await asyncio.sleep(0.3)  # Delay between months (faster but respectful)
            
            logger.info(f"[ATS/OU] ESPN fallback fetched {len(games)} completed games for {self.sport} {season}")
            return games
        
        except Exception as e:
            logger.error(f"[ATS/OU] Error in ESPN fallback: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _fetch_espn_games_by_date_range(
        self,
        espn_sport: str,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        Fetch completed games from ESPN for a date range.
        Uses ESPN scoreboard endpoint which returns games for a specific date.
        """
        games = []
        current_date = start_date
        
        while current_date <= end_date:
            try:
                # ESPN scoreboard endpoint format: /scoreboard?dates=YYYYMMDD
                date_str = current_date.strftime("%Y%m%d")
                
                # Get base URL for sport
                base_url = self.espn.SPORT_URLS.get(espn_sport)
                if not base_url:
                    current_date += timedelta(days=1)
                    continue
                
                # ESPN scoreboard endpoint
                # Note: ESPN scoreboard format may vary by sport
                if espn_sport.startswith("soccer"):
                    # Soccer uses date parameter in format: ?dates=YYYYMMDD
                    url = f"{base_url}/scoreboard?dates={date_str}"
                else:
                    url = f"{base_url}/scoreboard?dates={date_str}"
                
                # Use ESPN scraper's request method (has rate limiting built in)
                data = await self.espn._make_request(url)
                
                if data and 'events' in data:
                    for event in data.get('events', []):
                        competition = event.get('competitions', [{}])[0]
                        status = competition.get('status', {})
                        
                        # Only include completed games
                        if status.get('type', {}).get('completed', False):
                            competitors = competition.get('competitors', [])
                            
                            if len(competitors) >= 2:
                                home_comp = next(
                                    (c for c in competitors if c.get('homeAway') == 'home'),
                                    competitors[0]
                                )
                                away_comp = next(
                                    (c for c in competitors if c.get('homeAway') == 'away'),
                                    competitors[1]
                                )
                                
                                home_team = home_comp.get('team', {}).get('displayName', '')
                                away_team = away_comp.get('team', {}).get('displayName', '')
                                home_score = int(home_comp.get('score', 0))
                                away_score = int(away_comp.get('score', 0))
                                
                                # Parse game date
                                game_date_str = event.get('date', '')
                                try:
                                    game_date = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                                except:
                                    game_date = datetime.combine(current_date, datetime.min.time())
                                
                                games.append({
                                    'id': event.get('id', f"espn_{current_date}_{home_team}_{away_team}"),
                                    'home_team': home_team,
                                    'away_team': away_team,
                                    'home_score': home_score,
                                    'away_score': away_score,
                                    'game_date': game_date,
                                    'sport': self.sport,
                                })
                
                # Small delay between dates (faster path)
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.warning(f"[ATS/OU] Error fetching ESPN games for {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        return games
    
    async def _get_existing_game_results(self, season: str) -> List[GameResult]:
        """Get existing game results for this sport and season to avoid re-fetching"""
        result = await self.db.execute(
            select(GameResult).where(
                and_(
                    GameResult.sport == self.sport,
                    GameResult.game_date >= datetime(int(season), 1, 1, tzinfo=timezone.utc),
                    GameResult.game_date < datetime(int(season) + 1, 1, 1, tzinfo=timezone.utc),
                    GameResult.completed == 'true',
                    GameResult.home_score.isnot(None),
                    GameResult.away_score.isnot(None)
                )
            )
        )
        return result.scalars().all()
    
    async def _get_or_create_game_result(self, game_data: Dict) -> Optional[GameResult]:
        """Get or create GameResult record for a game"""
        # Try to find existing game result
        result = await self.db.execute(
            select(GameResult).where(
                GameResult.external_game_id == game_data.get('id')
            ).limit(1)
        )
        game_result = result.scalar_one_or_none()
        
        if game_result:
            # Update scores if different
            if game_result.home_score != game_data.get('home_score') or \
               game_result.away_score != game_data.get('away_score'):
                game_result.home_score = game_data.get('home_score')
                game_result.away_score = game_data.get('away_score')
                game_result.actual_total = game_data.get('home_score', 0) + game_data.get('away_score', 0)
        else:
            # Create new game result
            game_result = GameResult(
                external_game_id=game_data.get('id'),
                sport=game_data.get('sport', self.sport),
                home_team=game_data.get('home_team'),
                away_team=game_data.get('away_team'),
                game_date=game_data.get('game_date'),
                home_score=game_data.get('home_score'),
                away_score=game_data.get('away_score'),
                actual_total=game_data.get('home_score', 0) + game_data.get('away_score', 0),
                status='final',
                completed='true'
            )
            self.db.add(game_result)
            await self._flush_with_retry()
        
        return game_result
    
    async def _get_spread_and_total_lines(
        self,
        home_team: str,
        away_team: str,
        game_date: datetime,
        sport: str
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Get spread and total lines from database for a game.
        
        The Odds API stores spreads/totals in the outcome field as:
        - Spreads: "home +3.5" or "away -3.5" (point value is in outcome string)
        - Totals: "over 44.5" or "under 44.5" (point value is in outcome string)
        
        Returns:
            Tuple of (spread_line, total_line) or (None, None) if not found
        """
        # Find game in database
        game_result = await self.db.execute(
            select(Game).where(
                and_(
                    Game.home_team == home_team,
                    Game.away_team == away_team,
                    Game.sport == sport,
                    Game.start_time >= game_date - timedelta(days=1),
                    Game.start_time <= game_date + timedelta(days=1)
                )
            ).limit(1)
        )
        game = game_result.scalar_one_or_none()
        
        if not game:
            return None, None
        
        spread_line = None
        total_line = None
        
        # Get spread market
        spread_market_result = await self.db.execute(
            select(Market).where(
                and_(
                    Market.game_id == game.id,
                    Market.market_type == 'spreads'
                )
            ).limit(1)
        )
        spread_market = spread_market_result.scalar_one_or_none()
        
        if spread_market:
            # Get all spread odds to find the line
            spread_odds_result = await self.db.execute(
                select(Odds).where(
                    Odds.market_id == spread_market.id
                ).order_by(Odds.created_at.desc())
            )
            spread_odds = spread_odds_result.scalars().all()
            
            # Parse spread from outcome string (e.g., "home +3.5" or "away -3.5")
            for odd in spread_odds:
                outcome = odd.outcome.lower()
                if 'home' in outcome or home_team.lower() in outcome:
                    # Extract number from outcome (e.g., "+3.5" or "-3.5")
                    match = re.search(r'([+-]?\d+\.?\d*)', outcome)
                    if match:
                        try:
                            spread_line = float(match.group(1))
                            break  # Found home spread
                        except ValueError:
                            continue
        
        # Get total market
        total_market_result = await self.db.execute(
            select(Market).where(
                and_(
                    Market.game_id == game.id,
                    Market.market_type == 'totals'
                )
            ).limit(1)
        )
        total_market = total_market_result.scalar_one_or_none()
        
        if total_market:
            # Get all total odds to find the line
            total_odds_result = await self.db.execute(
                select(Odds).where(
                    Odds.market_id == total_market.id
                ).order_by(Odds.created_at.desc())
            )
            total_odds = total_odds_result.scalars().all()
            
            # Parse total from outcome string (e.g., "over 44.5" or "under 44.5")
            for odd in total_odds:
                outcome = odd.outcome.lower()
                if 'over' in outcome:
                    # Extract number from outcome
                    match = re.search(r'(\d+\.?\d*)', outcome)
                    if match:
                        try:
                            total_line = float(match.group(1))
                            break  # Found total line
                        except ValueError:
                            continue
        
        return spread_line, total_line
    
    def _calculate_ats(
        self,
        home_score: int,
        away_score: int,
        spread_line: float
    ) -> str:
        """
        Calculate if home team covered the spread.
        
        Args:
            home_score: Home team final score
            away_score: Away team final score
            spread_line: Spread line (negative means home is favorite)
        
        Returns:
            "yes" if home covered, "no" if away covered, "push" if tie
        """
        # Spread is from home team's perspective
        # Negative spread means home is favored (e.g., -3.5 means home must win by 4+)
        # Positive spread means away is favored (e.g., +3.5 means away can lose by 3 or less)
        
        actual_margin = home_score - away_score
        
        if spread_line < 0:
            # Home is favored
            # Home covers if they win by more than |spread_line|
            if actual_margin > abs(spread_line):
                return "yes"
            elif actual_margin < abs(spread_line):
                return "no"
            else:
                return "push"
        else:
            # Away is favored (positive spread)
            # Home covers if they win or lose by less than spread_line
            if actual_margin > spread_line:
                return "yes"
            elif actual_margin < spread_line:
                return "no"
            else:
                return "push"
    
    def _calculate_over_under(
        self,
        home_score: int,
        away_score: int,
        total_line: float
    ) -> str:
        """
        Calculate if total went over or under.
        
        Args:
            home_score: Home team final score
            away_score: Away team final score
            total_line: Total line (over/under)
        
        Returns:
            "over", "under", or "push"
        """
        actual_total = home_score + away_score
        
        if actual_total > total_line:
            return "over"
        elif actual_total < total_line:
            return "under"
        else:
            return "push"
    
    async def _update_team_stats(
        self,
        home_team: str,
        away_team: str,
        game_result: GameResult,
        season: str
    ):
        """Update TeamStats with ATS and Over/Under data for both teams"""
        
        # Update home team stats
        await self._update_single_team_stats(
            home_team,
            game_result,
            is_home=True,
            season=season
        )
        
        # Update away team stats
        await self._update_single_team_stats(
            away_team,
            game_result,
            is_home=False,
            season=season
        )
    
    async def _update_single_team_stats(
        self,
        team_name: str,
        game_result: GameResult,
        is_home: bool,
        season: str
    ):
        """Update ATS and Over/Under stats for a single team"""
        
        # Get or create team stats
        result = await self.db.execute(
            select(TeamStats).where(
                and_(
                    TeamStats.team_name == team_name,
                    TeamStats.season == season,
                    TeamStats.week.is_(None)  # Season totals
                )
            ).limit(1)
        )
        team_stats = result.scalar_one_or_none()
        
        if not team_stats:
            # Create new team stats record
            team_stats = TeamStats(
                team_name=team_name,
                season=season,
                week=None
            )
            self.db.add(team_stats)
            await self.db.flush()
        
        # Note: ATS/OU calculation logic is the same for all sports
        
        # Update ATS stats
        if game_result.home_covered_spread and game_result.spread_line is not None:
            if is_home:
                # Home team perspective
                if game_result.home_covered_spread == "yes":
                    team_stats.ats_wins += 1
                    team_stats.ats_home_wins += 1
                elif game_result.home_covered_spread == "no":
                    team_stats.ats_losses += 1
                    team_stats.ats_home_losses += 1
                else:  # push
                    team_stats.ats_pushes += 1
            else:
                # Away team perspective (opposite of home)
                if game_result.home_covered_spread == "no":
                    team_stats.ats_wins += 1
                    team_stats.ats_away_wins += 1
                elif game_result.home_covered_spread == "yes":
                    team_stats.ats_losses += 1
                    team_stats.ats_away_losses += 1
                else:  # push
                    team_stats.ats_pushes += 1
        
        # Update Over/Under stats
        if game_result.total_over_under and game_result.actual_total:
            if game_result.total_over_under == "over":
                team_stats.over_wins += 1
            elif game_result.total_over_under == "under":
                team_stats.under_wins += 1
            
            # Update average total points
            total_games = team_stats.over_wins + team_stats.under_wins
            if total_games > 0:
                # Recalculate average (simplified - in production, maintain running average)
                current_avg = team_stats.avg_total_points or 0.0
                team_stats.avg_total_points = ((current_avg * (total_games - 1)) + game_result.actual_total) / total_games
        
        # Recalculate percentages
        ats_total = team_stats.ats_wins + team_stats.ats_losses
        if ats_total > 0:
            team_stats.ats_win_percentage = (team_stats.ats_wins / ats_total) * 100.0
        
        ou_total = team_stats.over_wins + team_stats.under_wins
        if ou_total > 0:
            team_stats.over_percentage = (team_stats.over_wins / ou_total) * 100.0
        
        # Update recent trends (last 5 games)
        await self._update_recent_trends(team_name, season)
        
        await self._flush_with_retry()
    
    async def _update_recent_trends(self, team_name: str, season: str):
        """Update recent ATS and Over/Under trends (last 5 games)"""
        # Get last 5 completed games for this team
        result = await self.db.execute(
            select(GameResult).where(
                and_(
                    or_(
                        GameResult.home_team == team_name,
                        GameResult.away_team == team_name
                    ),
                    GameResult.sport == self.sport,
                    GameResult.completed == 'true',
                    GameResult.home_score.isnot(None),
                    GameResult.away_score.isnot(None)
                )
            ).order_by(desc(GameResult.game_date)).limit(5)
        )
        recent_games = result.scalars().all()
        
        if not recent_games:
            return
        
        # Get team stats
        stats_result = await self.db.execute(
            select(TeamStats).where(
                and_(
                    TeamStats.team_name == team_name,
                    TeamStats.season == season,
                    TeamStats.week.is_(None)
                )
            ).limit(1)
        )
        team_stats = stats_result.scalar_one_or_none()
        
        if not team_stats:
            return
        
        # Calculate recent ATS
        recent_ats_wins = 0
        recent_ats_losses = 0
        recent_overs = 0
        recent_unders = 0
        
        for game in recent_games:
            is_home = game.home_team == team_name
            
            # ATS
            if game.home_covered_spread and game.spread_line is not None:
                if is_home:
                    if game.home_covered_spread == "yes":
                        recent_ats_wins += 1
                    elif game.home_covered_spread == "no":
                        recent_ats_losses += 1
                else:
                    if game.home_covered_spread == "no":
                        recent_ats_wins += 1
                    elif game.home_covered_spread == "yes":
                        recent_ats_losses += 1
            
            # Over/Under
            if game.total_over_under:
                if game.total_over_under == "over":
                    recent_overs += 1
                elif game.total_over_under == "under":
                    recent_unders += 1
        
        team_stats.ats_recent_wins = recent_ats_wins
        team_stats.ats_recent_losses = recent_ats_losses
        team_stats.over_recent_count = recent_overs
        team_stats.under_recent_count = recent_unders

