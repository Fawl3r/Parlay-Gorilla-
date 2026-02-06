"""Stats scraper service for team data, weather, and injuries"""

import httpx
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import json

from app.core.config import settings
from app.models.team_stats import TeamStats
from app.models.game import Game
from app.services.data_fetchers.espn_scraper import ESPNScraper
from app.repositories.sports_data_repository import SportsDataRepository
from app.repositories.apisports_injury_repository import ApisportsInjuryRepository
from app.services.apisports.team_mapper import get_team_mapper
from app.services.apisports.data_adapter import ApiSportsDataAdapter
from app.services.apisports.injury_parser import (
    LEAGUE_TO_SPORT_KEY,
    apisports_injury_payload_to_canonical,
)
from app.services.stats.snapshot_manager import SnapshotManager
from app.services.stats.normalizer import StatsNormalizer
from app.services.stats.features.team_feature_builder import TeamFeatureBuilder
from app.services.stats.features.injury_feature_builder import InjuryFeatureBuilder
from app.services.stats.data_quality import DataQualityScorer
from app.services.stats.fallback_manager import FallbackManager, FetchContext
from app.services.sports.sport_registry import get_season_mode, get_sport_capability, SeasonMode
from datetime import timezone


class StatsScraperService:
    """Service for scraping and aggregating team statistics, weather, and injury data"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.weather_api_key = settings.openweather_api_key
        self._cache: Dict[str, tuple] = {}  # Simple in-memory cache: key -> (data, timestamp)
        self._cache_ttl = 900  # 15 minutes cache (reduced from 1 hour to ensure fresher data)
        
        # API-Sports integration
        self._apisports_repo = SportsDataRepository(db)
        self._team_mapper = get_team_mapper()
        self._data_adapter = ApiSportsDataAdapter()
    
    async def get_team_stats(
        self,
        team_name: str,
        season: str,
        week: Optional[int] = None,
        bypass_cache: bool = False
    ) -> Optional[Dict]:
        """
        Get team statistics from database or calculate from game results
        
        Args:
            team_name: Name of the team
            season: Season year (e.g., "2024")
            week: Optional week number
            bypass_cache: If True, skip cache and fetch fresh from database
        
        Returns dict with:
        - Record (wins, losses, win_pct)
        - Offensive stats (ppg, ypg, etc.)
        - Defensive stats (papg, yapg, etc.)
        - ATS trends (ats_wins, ats_losses, ats_pct)
        - O/U trends (over_wins, under_wins, over_pct)
        - Recent form (last 5 games)
        """
        cache_key = f"team_stats:{team_name}:{season}:{week or 'season'}"
        
        # Check cache (unless bypassing)
        if not bypass_cache:
            if cache_key in self._cache:
                data, timestamp = self._cache[cache_key]
                if (datetime.now() - timestamp).total_seconds() < self._cache_ttl:
                    return data
        
        # Query database
        query = select(TeamStats).where(
            TeamStats.team_name == team_name,
            TeamStats.season == season
        )
        if week:
            query = query.where(TeamStats.week == week)
        else:
            query = query.where(TeamStats.week.is_(None))
        
        result = await self.db.execute(query)
        team_stats = result.scalar_one_or_none()
        
        if team_stats:
            stats_dict = {
                "team_name": team_stats.team_name,
                "season": team_stats.season,
                "week": team_stats.week,
                "record": {
                    "wins": team_stats.wins,
                    "losses": team_stats.losses,
                    "ties": team_stats.ties,
                    "win_percentage": team_stats.win_percentage,
                },
                "offense": {
                    "points_per_game": team_stats.points_per_game,
                    "yards_per_game": team_stats.yards_per_game,
                    "passing_yards_per_game": team_stats.passing_yards_per_game,
                    "rushing_yards_per_game": team_stats.rushing_yards_per_game,
                },
                "defense": {
                    "points_allowed_per_game": team_stats.points_allowed_per_game,
                    "yards_allowed_per_game": team_stats.yards_allowed_per_game,
                    "turnovers_forced": team_stats.turnovers_forced,
                },
                "recent_form": {
                    "recent_wins": team_stats.recent_wins,
                    "recent_losses": team_stats.recent_losses,
                    "home_record": f"{team_stats.home_record_wins}-{team_stats.home_record_losses}",
                    "away_record": f"{team_stats.away_record_wins}-{team_stats.away_record_losses}",
                },
                "strength_ratings": {
                    "offensive_rating": team_stats.offensive_rating,
                    "defensive_rating": team_stats.defensive_rating,
                    "overall_rating": team_stats.overall_rating,
                },
                "ats_trends": {
                    "wins": team_stats.ats_wins,
                    "losses": team_stats.ats_losses,
                    "pushes": team_stats.ats_pushes,
                    "win_percentage": team_stats.ats_win_percentage,
                    "recent": f"{team_stats.ats_recent_wins}-{team_stats.ats_recent_losses}",
                    "home": f"{team_stats.ats_home_wins}-{team_stats.ats_home_losses}",
                    "away": f"{team_stats.ats_away_wins}-{team_stats.ats_away_losses}",
                },
                "over_under_trends": {
                    "overs": team_stats.over_wins,
                    "unders": team_stats.under_wins,
                    "over_percentage": team_stats.over_percentage,
                    "recent_overs": team_stats.over_recent_count,
                    "recent_unders": team_stats.under_recent_count,
                    "avg_total_points": team_stats.avg_total_points,
                },
            }
            
            # Cache it
            self._cache[cache_key] = (stats_dict, datetime.now())
            return stats_dict
        
        # Return None if not found in database
        # External API fetching is handled in get_matchup_data() which has access to league code
        return None
    
    async def fetch_and_store_team_stats(
        self,
        team_name: str,
        league: str,
        season: str,
        week: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Fetch team stats from external APIs and store in database
        
        Args:
            team_name: Team name
            league: League code (NFL, NBA, NHL, MLB, etc.)
            season: Season year (e.g., "2024")
            week: Optional week number
            
        Returns:
            Dict with team stats or None if fetch failed
        """
        try:
            # Map league to sport code
            league_to_sport = {
                "NFL": "americanfootball_nfl",
                "NBA": "basketball_nba",
                "NHL": "icehockey_nhl",
                "MLB": "baseball_mlb",
                "EPL": "football",
                "LALIGA": "football",
                "MLS": "football",
                "UCL": "football",
                "SOCCER": "football",
            }
            
            sport_code_map = {
                "NFL": "nfl",
                "NBA": "nba",
                "NHL": "nhl",
                "MLB": "mlb",
                "EPL": "epl",
                "LALIGA": "laliga",
                "MLS": "mls",
                "UCL": "ucl",
                "SOCCER": "soccer",
            }
            
            sport_key = league_to_sport.get(league.upper())
            sport_code = sport_code_map.get(league.upper())
            
            if not sport_key:
                print(f"[StatsScraper] Unsupported league: {league}")
                return None
            
            espn = ESPNScraper()
            
            # Try API-Sports first
            external_stats = None
            team_id = self._team_mapper.get_team_id(team_name, sport_key)
            if team_id:
                try:
                    print(f"[StatsScraper] Fetching stats from API-Sports for {team_name} (ID: {team_id})")
                    team_stat = await self._apisports_repo.get_team_stats(sport_key, team_id)
                    if team_stat and team_stat.payload_json:
                        external_stats = self._data_adapter.team_stats_to_internal_format(
                            team_stat.payload_json,
                            team_id,
                            sport_key,
                            team_stat.season
                        )
                        print(f"[StatsScraper] Successfully fetched API-Sports stats for {team_name}")
                except Exception as e:
                    print(f"[StatsScraper] API-Sports stats fetch failed for {team_name}: {e}")
            
            # Fallback to ESPN if API-Sports fails
            if not external_stats:
                try:
                    print(f"[StatsScraper] Fetching stats from ESPN for {team_name}")
                    external_stats = await espn.scrape_team_stats(team_name, sport_code or "nfl")
                except Exception as e:
                    print(f"[StatsScraper] ESPN stats fetch failed for {team_name}: {e}")
            
            if not external_stats:
                print(f"[StatsScraper] Failed to fetch stats for {team_name} from both sources")
                return None
            
            # Convert to internal format
            stats_dict = self._convert_external_stats(external_stats, team_name, season, week)
            
            # Store in database
            await self._store_team_stats_in_db(stats_dict)
            
            return stats_dict
            
        except Exception as e:
            print(f"[StatsScraper] Error fetching/storing stats for {team_name}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _store_team_stats_in_db(self, stats_dict: Dict):
        """
        Store team stats in database
        
        Args:
            stats_dict: Stats dictionary from _convert_external_stats
        """
        try:
            from sqlalchemy import and_
            
            # Get or create team stats record
            result = await self.db.execute(
                select(TeamStats).where(
                    and_(
                        TeamStats.team_name == stats_dict["team_name"],
                        TeamStats.season == stats_dict["season"],
                        TeamStats.week == stats_dict.get("week")
                    )
                )
            )
            team_stats = result.scalar_one_or_none()
            
            if not team_stats:
                # Create new record
                team_stats = TeamStats(
                    team_name=stats_dict["team_name"],
                    season=stats_dict["season"],
                    week=stats_dict.get("week")
                )
                self.db.add(team_stats)
            
            # Update record fields
            record = stats_dict.get("record", {})
            team_stats.wins = record.get("wins", 0)
            team_stats.losses = record.get("losses", 0)
            team_stats.ties = record.get("ties", 0)
            team_stats.win_percentage = record.get("win_percentage", 0.0)
            
            # Update offensive stats
            offense = stats_dict.get("offense", {})
            team_stats.points_per_game = offense.get("points_per_game", 0.0)
            team_stats.yards_per_game = offense.get("yards_per_game", 0.0)
            team_stats.passing_yards_per_game = offense.get("passing_yards_per_game", 0.0)
            team_stats.rushing_yards_per_game = offense.get("rushing_yards_per_game", 0.0)
            
            # Update defensive stats
            defense = stats_dict.get("defense", {})
            team_stats.points_allowed_per_game = defense.get("points_allowed_per_game", 0.0)
            team_stats.yards_allowed_per_game = defense.get("yards_allowed_per_game", 0.0)
            team_stats.turnovers_forced = defense.get("turnovers_forced", 0)
            
            # Update recent form
            recent_form = stats_dict.get("recent_form", {})
            team_stats.recent_wins = recent_form.get("recent_wins", 0)
            team_stats.recent_losses = recent_form.get("recent_losses", 0)
            
            # Parse home/away records
            home_record = recent_form.get("home_record", "0-0")
            if isinstance(home_record, str) and "-" in home_record:
                parts = home_record.split("-")
                if len(parts) == 2:
                    team_stats.home_record_wins = int(parts[0]) if parts[0].isdigit() else 0
                    team_stats.home_record_losses = int(parts[1]) if parts[1].isdigit() else 0
            
            away_record = recent_form.get("away_record", "0-0")
            if isinstance(away_record, str) and "-" in away_record:
                parts = away_record.split("-")
                if len(parts) == 2:
                    team_stats.away_record_wins = int(parts[0]) if parts[0].isdigit() else 0
                    team_stats.away_record_losses = int(parts[1]) if parts[1].isdigit() else 0
            
            # Update strength ratings
            strength = stats_dict.get("strength_ratings", {})
            team_stats.offensive_rating = strength.get("offensive_rating", 0.0)
            team_stats.defensive_rating = strength.get("defensive_rating", 0.0)
            team_stats.overall_rating = strength.get("overall_rating", 0.0)
            
            await self.db.flush()
            print(f"[StatsScraper] ✓ Stored stats for {stats_dict['team_name']} ({stats_dict['season']})")
            
        except Exception as e:
            print(f"[StatsScraper] Error storing team stats in DB: {e}")
            import traceback
            traceback.print_exc()
            await self.db.rollback()
    
    def _convert_external_stats(self, external_stats: Dict, team_name: str, season: str, week: Optional[int]) -> Dict:
        """Convert API-Sports/ESPN stats format to our internal format"""
        # Extract offense and defense from external stats
        offense = external_stats.get("offense", {})
        defense = external_stats.get("defense", {})
        record = external_stats.get("record", {})
        
        # Helper to extract value from ESPN format (nested dict with 'value' key) or direct value
        def extract_value(data, *keys):
            """Extract value from nested dict, handling ESPN format with 'value' keys"""
            current = data
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                else:
                    return 0
            # If current is a dict with 'value' key (ESPN format), extract it
            if isinstance(current, dict) and 'value' in current:
                try:
                    return float(current['value']) if current['value'] else 0
                except (ValueError, TypeError):
                    return 0
            # Otherwise, try to convert directly
            try:
                return float(current) if current else 0
            except (ValueError, TypeError):
                return 0
        
        # Handle nested API-Sports/ESPN format
        # Some sources return nested structures like offense.passing.yards_per_game
        passing = offense.get("passing", {}) if isinstance(offense.get("passing"), dict) else {}
        rushing = offense.get("rushing", {}) if isinstance(offense.get("rushing"), dict) else {}
        
        # Extract PPG - try multiple possible field names and formats
        ppg = (
            extract_value(offense, "points_per_game") or
            extract_value(offense, "ppg") or
            # ESPN format: look for keys containing "points" and "game"
            next((extract_value(offense, k) for k in offense.keys() if "point" in k.lower() and "game" in k.lower()), 0) or
            0
        )
        
        # Extract YPG - try multiple possible field names
        ypg = 0.0
        # Try direct keys first
        if extract_value(offense, "yards_per_game"):
            ypg = extract_value(offense, "yards_per_game")
        elif extract_value(offense, "total_yards_per_game"):
            ypg = extract_value(offense, "total_yards_per_game")
        elif extract_value(offense, "ypg"):
            ypg = extract_value(offense, "ypg")
        else:
            # ESPN format: look for keys containing "yards" and "game" (try without "total" requirement)
            for k in offense.keys():
                k_lower = k.lower()
                if "yard" in k_lower and "game" in k_lower:
                    val = extract_value(offense, k)
                    if val and val > 0:
                        ypg = val
                        break
            # If still 0, try any key with "total" and "yard"
            if ypg == 0:
                for k in offense.keys():
                    k_lower = k.lower()
                    if "total" in k_lower and "yard" in k_lower:
                        val = extract_value(offense, k)
                        if val and val > 0:
                            ypg = val
                            break
        
        # Extract passing yards
        pass_ypg = (
            extract_value(offense, "passing_yards_per_game") or
            extract_value(passing, "yards_per_game") or
            extract_value(passing, "ypg") or
            # ESPN format: look for keys containing "pass" and "yard"
            next((extract_value(offense, k) for k in offense.keys() if "pass" in k.lower() and "yard" in k.lower()), 0) or
            0
        )
        
        # Extract rushing yards
        rush_ypg = (
            extract_value(offense, "rushing_yards_per_game") or
            extract_value(rushing, "yards_per_game") or
            extract_value(rushing, "ypg") or
            # ESPN format: look for keys containing "rush" and "yard"
            next((extract_value(offense, k) for k in offense.keys() if "rush" in k.lower() and "yard" in k.lower()), 0) or
            0
        )
        
        # Handle defensive stats - some sources use "points_per_game" for defense (points allowed)
        defense_passing = defense.get("passing_allowed", {}) if isinstance(defense.get("passing_allowed"), dict) else {}
        defense_rushing = defense.get("rushing_allowed", {}) if isinstance(defense.get("rushing_allowed"), dict) else {}
        
        papg = (
            extract_value(defense, "points_allowed_per_game") or
            extract_value(defense, "points_per_game") or  # Some sources use this
            extract_value(defense, "papg") or
            # ESPN format: look for keys containing "point" and "allowed" or "against"
            next((extract_value(defense, k) for k in defense.keys() if ("point" in k.lower() and ("allowed" in k.lower() or "against" in k.lower()))), 0) or
            0
        )
        
        yapg = 0.0
        # Try direct keys first
        if extract_value(defense, "yards_allowed_per_game"):
            yapg = extract_value(defense, "yards_allowed_per_game")
        elif extract_value(defense, "yards_per_game"):  # some sources use this
            yapg = extract_value(defense, "yards_per_game")
        elif extract_value(defense, "yapg"):
            yapg = extract_value(defense, "yapg")
        else:
            # ESPN format: look for keys containing "yard" and "allowed" or "against"
            for k in defense.keys():
                k_lower = k.lower()
                if "yard" in k_lower and ("allowed" in k_lower or "against" in k_lower):
                    val = extract_value(defense, k)
                    if val and val > 0:
                        yapg = val
                        break
        
        turnovers_forced = (
            extract_value(defense, "turnovers_forced") or
            extract_value(defense, "takeaways") or  # Some sources use this
            # ESPN format: look for keys containing "turnover" or "takeaway"
            next((extract_value(defense, k) for k in defense.keys() if ("turnover" in k.lower() or "takeaway" in k.lower())), 0) or
            0
        )
        
        # Handle situational records
        situational = external_stats.get("situational", {})
        home_record = situational.get("home_record", {})
        away_record = situational.get("away_record", {})
        
        # Format home/away records
        if isinstance(home_record, dict):
            home_wins = home_record.get("wins", 0)
            home_losses = home_record.get("losses", 0)
            home_record_str = f"{home_wins}-{home_losses}"
        else:
            home_record_str = str(home_record) if home_record else "0-0"
            
        if isinstance(away_record, dict):
            away_wins = away_record.get("wins", 0)
            away_losses = away_record.get("losses", 0)
            away_record_str = f"{away_wins}-{away_losses}"
        else:
            away_record_str = str(away_record) if away_record else "0-0"
        
        return {
            "team_name": team_name,
            "season": season,
            "week": week,
            "record": {
                "wins": record.get("wins", 0),
                "losses": record.get("losses", 0),
                "ties": record.get("ties", 0),
                "win_percentage": record.get("win_percentage", 0.0),
            },
            "offense": {
                "points_per_game": float(ppg) if ppg else 0.0,
                "yards_per_game": float(ypg) if ypg else 0.0,
                "passing_yards_per_game": float(pass_ypg) if pass_ypg else 0.0,
                "rushing_yards_per_game": float(rush_ypg) if rush_ypg else 0.0,
            },
            "defense": {
                "points_allowed_per_game": float(papg) if papg else 0.0,
                "yards_allowed_per_game": float(yapg) if yapg else 0.0,
                "turnovers_forced": int(turnovers_forced) if turnovers_forced else 0,
            },
            "recent_form": {
                "recent_wins": 0,  # Would need to fetch separately
                "recent_losses": 0,
                "home_record": home_record_str,
                "away_record": away_record_str,
            },
            "strength_ratings": {
                "offensive_rating": external_stats.get("advanced", {}).get("offensive_rating", 0.0),
                "defensive_rating": external_stats.get("advanced", {}).get("defensive_rating", 0.0),
                "overall_rating": external_stats.get("advanced", {}).get("net_rating", 0.0),
            },
            "ats_trends": {
                "wins": 0,  # Would need to calculate from game results
                "losses": 0,
                "pushes": 0,
                "win_percentage": 0.0,
                "recent": "0-0",
                "home": "0-0",
                "away": "0-0",
            },
            "over_under_trends": {
                "overs": 0,
                "unders": 0,
                "over_percentage": 0.0,
                "recent_overs": 0,
                "recent_unders": 0,
                "avg_total_points": 0.0,
            },
        }

    async def _get_ats_ou_from_legacy(self, team_name: str, season: str) -> Optional[Dict]:
        """Load ATS and over/under trends from legacy team_stats table (season totals, week=None)."""
        query = select(TeamStats).where(
            TeamStats.team_name == team_name,
            TeamStats.season == season,
            TeamStats.week.is_(None),
        ).limit(1)
        result = await self.db.execute(query)
        row = result.scalar_one_or_none()
        if not row:
            return None
        return {
            "ats_trends": {
                "wins": row.ats_wins,
                "losses": row.ats_losses,
                "pushes": row.ats_pushes,
                "win_percentage": row.ats_win_percentage,
                "recent": f"{row.ats_recent_wins}-{row.ats_recent_losses}",
                "home": f"{row.ats_home_wins}-{row.ats_home_losses}",
                "away": f"{row.ats_away_wins}-{row.ats_away_losses}",
            },
            "over_under_trends": {
                "overs": row.over_wins,
                "unders": row.under_wins,
                "over_percentage": row.over_percentage,
                "recent_overs": row.over_recent_count,
                "recent_unders": row.under_recent_count,
                "avg_total_points": row.avg_total_points,
            },
        }

    async def get_team_bundle(
        self,
        team_name: str,
        sport: str,
        season: str,
        context: FetchContext,
    ) -> Dict:
        """
        Get comprehensive team data bundle using stats platform v2.
        
        Returns:
            {
                "canonical_stats": Dict,
                "injury_json": Dict,
                "derived_features": Dict,
                "data_quality": Dict,
                "source_flags": List[str],
            }
        """
        # Initialize services
        snapshot_manager = SnapshotManager(self.db)
        normalizer = StatsNormalizer(self.db)
        team_feature_builder = TeamFeatureBuilder(self.db)
        injury_feature_builder = InjuryFeatureBuilder()
        data_quality_scorer = DataQualityScorer()
        fallback_manager = FallbackManager()
        
        # Determine season mode if not provided
        if context.season_mode is None:
            context.season_mode = get_season_mode(sport, datetime.now(timezone.utc))
        
        source_flags = []
        
        # Try to get current stats from DB
        canonical_stats = await normalizer.get_current_stats(team_name, sport, season)
        stats_updated_at = None
        stats_freshness_hours = float('inf')
        
        if canonical_stats:
            # Get updated_at from DB
            from sqlalchemy import text
            result = await self.db.execute(
                text("""
                    SELECT updated_at FROM team_stats_current
                    WHERE team_name = :team_name AND sport = :sport AND season = :season
                """),
                {"team_name": team_name, "sport": sport, "season": season}
            )
            row = result.fetchone()
            if row:
                stats_updated_at = row[0]
                stats_freshness_hours = (datetime.now(timezone.utc) - stats_updated_at).total_seconds() / 3600.0
            source_flags.append("db")
        else:
            # No stats in DB - check if we should fetch
            if fallback_manager.should_fetch_stats(0.0, context, data_missing=True):
                # Fetch from external API
                try:
                    raw_stats = await self.get_team_stats(team_name, season)
                    if raw_stats:
                        # Save snapshot
                        await snapshot_manager.save_stats_snapshot(
                            team_name, sport, season, "api_espn", raw_stats
                        )
                        # Normalize and update current
                        canonical_stats = await normalizer.normalize_and_update_stats(
                            team_name, sport, season, raw_stats
                        )
                        stats_updated_at = datetime.now(timezone.utc)
                        stats_freshness_hours = 0.0
                        source_flags.append("api_espn")
                except Exception as e:
                    print(f"[StatsScraper] Error fetching stats for {team_name}: {e}")
        
        # If still no stats and off-season, try last completed season
        if not canonical_stats and context.season_mode == SeasonMode.OFF_SEASON:
            from app.services.sports.sport_registry import get_last_completed_season
            last_season = get_last_completed_season(sport, datetime.now(timezone.utc))
            if last_season:
                canonical_stats = await normalizer.get_current_stats(team_name, sport, last_season)
                if canonical_stats:
                    source_flags.append("db_last_season")
        
        # Default empty stats if still None
        if not canonical_stats:
            canonical_stats = {}

        # Merge ATS/OU from legacy team_stats table so v2 bundle matches what CoreAnalysisGenerator._build_trends expects
        ats_ou = await self._get_ats_ou_from_legacy(team_name, season)
        if ats_ou:
            canonical_stats["ats_trends"] = ats_ou["ats_trends"]
            canonical_stats["over_under_trends"] = ats_ou["over_under_trends"]
        elif "ats_trends" not in canonical_stats:
            canonical_stats["ats_trends"] = {
                "wins": 0, "losses": 0, "pushes": 0, "win_percentage": 0.0,
                "recent": "0-0", "home": "0-0", "away": "0-0",
            }
        if "over_under_trends" not in canonical_stats:
            canonical_stats["over_under_trends"] = {
                "overs": 0, "unders": 0, "over_percentage": 0.0,
                "recent_overs": 0, "recent_unders": 0, "avg_total_points": 0.0,
            }
        
        # Get current injuries from DB
        canonical_injuries = await normalizer.get_current_injuries(team_name, sport, season)
        injuries_updated_at = None
        injuries_freshness_hours = float('inf')
        previous_injuries = None
        
        if canonical_injuries:
            from sqlalchemy import text
            result = await self.db.execute(
                text("""
                    SELECT updated_at FROM injury_current
                    WHERE team_name = :team_name AND sport = :sport AND season = :season
                """),
                {"team_name": team_name, "sport": sport, "season": season}
            )
            row = result.fetchone()
            if row:
                injuries_updated_at = row[0]
                injuries_freshness_hours = (datetime.now(timezone.utc) - injuries_updated_at).total_seconds() / 3600.0
            source_flags.append("db")
            
            # Get previous snapshot for trend detection
            previous_snapshot = await snapshot_manager.get_latest_injury_snapshot(
                team_name, sport, season
            )
            if previous_snapshot:
                # Normalize previous snapshot for comparison
                capability = get_sport_capability(sport)
                previous_injuries = await normalizer.normalize_and_update_injuries(
                    team_name, sport, season, previous_snapshot
                )
        else:
            # No injuries in DB - check if we should fetch
            if fallback_manager.should_fetch_injuries(0.0, context, data_missing=True):
                try:
                    raw_injuries = await self.get_injury_report(team_name, sport)
                    if raw_injuries:
                        # Save snapshot
                        await snapshot_manager.save_injury_snapshot(
                            team_name, sport, season, "api_espn", raw_injuries
                        )
                        # Normalize and update current
                        canonical_injuries = await normalizer.normalize_and_update_injuries(
                            team_name, sport, season, raw_injuries
                        )
                        injuries_updated_at = datetime.now(timezone.utc)
                        injuries_freshness_hours = 0.0
                        source_flags.append("api_espn")
                except Exception as e:
                    print(f"[StatsScraper] Error fetching injuries for {team_name}: {e}")
        
        # Default empty injuries if still None
        if not canonical_injuries:
            canonical_injuries = {
                "unit_counts": {},
                "impact_scores": {"offense_impact": 0.0, "defense_impact": 0.0, "overall_impact": 0.0, "uncertainty": 1.0},
                "trend": "stable",
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        
        # Build injury features
        canonical_injuries = injury_feature_builder.build_impact_scores(
            canonical_injuries, sport, previous_injuries
        )
        
        # Build team features
        derived_features = await team_feature_builder.build_features(
            team_name, sport, season, canonical_stats
        )
        
        # Calculate data quality
        data_quality = data_quality_scorer.calculate_quality(
            updated_at=stats_updated_at or injuries_updated_at or datetime.now(timezone.utc),
            canonical_stats=canonical_stats,
            canonical_injuries=canonical_injuries,
            sources_used=source_flags,
        )
        
        # Update team_features_current
        from sqlalchemy import text
        await self.db.execute(
            text("""
                INSERT INTO team_features_current
                (team_name, sport, season, updated_at, features_json, data_quality_json)
                VALUES
                (:team_name, :sport, :season, :updated_at, :features_json, :data_quality_json)
                ON CONFLICT (team_name, sport, season)
                DO UPDATE SET
                    updated_at = :updated_at,
                    features_json = :features_json,
                    data_quality_json = :data_quality_json
            """),
            {
                "team_name": team_name,
                "sport": sport,
                "season": season,
                "updated_at": datetime.now(timezone.utc),
                "features_json": derived_features,
                "data_quality_json": data_quality,
            }
        )
        await self.db.flush()
        
        return {
            "canonical_stats": canonical_stats,
            "injury_json": canonical_injuries,
            "derived_features": derived_features,
            "data_quality": data_quality,
            "source_flags": source_flags,
        }

    def _zero_stats(self, team_name: str, season: str, week: Optional[int]) -> Dict:
        """Return a zeroed stats structure to avoid 'not available' output."""
        return {
            "team_name": team_name,
            "season": season,
            "week": week,
            "record": {
                "wins": 0,
                "losses": 0,
                "ties": 0,
                "win_percentage": 0.0,
            },
            "offense": {
                "points_per_game": 0.0,
                "yards_per_game": 0.0,
                "passing_yards_per_game": 0.0,
                "rushing_yards_per_game": 0.0,
            },
            "defense": {
                "points_allowed_per_game": 0.0,
                "yards_allowed_per_game": 0.0,
                "turnovers_forced": 0,
            },
            "recent_form": {
                "recent_wins": 0,
                "recent_losses": 0,
                "home_record": "0-0",
                "away_record": "0-0",
            },
            "strength_ratings": {
                "offensive_rating": 0.0,
                "defensive_rating": 0.0,
                "overall_rating": 0.0,
            },
            "ats_trends": {
                "wins": 0,
                "losses": 0,
                "pushes": 0,
                "win_percentage": 0.0,
                "recent": "0-0",
                "home": "0-0",
                "away": "0-0",
            },
            "over_under_trends": {
                "overs": 0,
                "unders": 0,
                "over_percentage": 0.0,
                "recent_overs": 0,
                "recent_unders": 0,
                "avg_total_points": 0.0,
            },
        }
    
    async def get_team_bundle(
        self,
        team_name: str,
        sport: str,
        season: str,
        context: FetchContext,
    ) -> Dict:
        """
        Get comprehensive team data bundle using stats platform v2.
        
        Returns:
            {
                "canonical_stats": Dict,
                "injury_json": Dict,
                "derived_features": Dict,
                "data_quality": Dict,
                "source_flags": List[str],
            }
        """
        # Initialize services
        snapshot_manager = SnapshotManager(self.db)
        normalizer = StatsNormalizer(self.db)
        team_feature_builder = TeamFeatureBuilder(self.db)
        injury_feature_builder = InjuryFeatureBuilder()
        data_quality_scorer = DataQualityScorer()
        fallback_manager = FallbackManager()
        
        # Determine season mode if not provided
        if context.season_mode is None:
            context.season_mode = get_season_mode(sport, datetime.now(timezone.utc))
        
        source_flags = []
        
        # Try to get current stats from DB
        canonical_stats = await normalizer.get_current_stats(team_name, sport, season)
        stats_updated_at = None
        stats_freshness_hours = float('inf')
        
        if canonical_stats:
            # Get updated_at from DB
            from sqlalchemy import text
            result = await self.db.execute(
                text("""
                    SELECT updated_at FROM team_stats_current
                    WHERE team_name = :team_name AND sport = :sport AND season = :season
                """),
                {"team_name": team_name, "sport": sport, "season": season}
            )
            row = result.fetchone()
            if row:
                stats_updated_at = row[0]
                stats_freshness_hours = (datetime.now(timezone.utc) - stats_updated_at).total_seconds() / 3600.0
            source_flags.append("db")
        else:
            # No stats in DB - check if we should fetch
            if fallback_manager.should_fetch_stats(0.0, context, data_missing=True):
                # Fetch from external API
                try:
                    raw_stats = await self.get_team_stats(team_name, season)
                    if raw_stats:
                        # Save snapshot
                        await snapshot_manager.save_stats_snapshot(
                            team_name, sport, season, "api_espn", raw_stats
                        )
                        # Normalize and update current
                        canonical_stats = await normalizer.normalize_and_update_stats(
                            team_name, sport, season, raw_stats
                        )
                        stats_updated_at = datetime.now(timezone.utc)
                        stats_freshness_hours = 0.0
                        source_flags.append("api_espn")
                except Exception as e:
                    print(f"[StatsScraper] Error fetching stats for {team_name}: {e}")
        
        # If still no stats and off-season, try last completed season
        if not canonical_stats and context.season_mode == SeasonMode.OFF_SEASON:
            from app.services.sports.sport_registry import get_last_completed_season
            last_season = get_last_completed_season(sport, datetime.now(timezone.utc))
            if last_season:
                canonical_stats = await normalizer.get_current_stats(team_name, sport, last_season)
                if canonical_stats:
                    source_flags.append("db_last_season")
        
        # Default empty stats if still None
        if not canonical_stats:
            canonical_stats = {}

        # Merge ATS/OU from legacy team_stats table so v2 bundle matches what CoreAnalysisGenerator._build_trends expects
        ats_ou = await self._get_ats_ou_from_legacy(team_name, season)
        if ats_ou:
            canonical_stats["ats_trends"] = ats_ou["ats_trends"]
            canonical_stats["over_under_trends"] = ats_ou["over_under_trends"]
        elif "ats_trends" not in canonical_stats:
            canonical_stats["ats_trends"] = {
                "wins": 0, "losses": 0, "pushes": 0, "win_percentage": 0.0,
                "recent": "0-0", "home": "0-0", "away": "0-0",
            }
        if "over_under_trends" not in canonical_stats:
            canonical_stats["over_under_trends"] = {
                "overs": 0, "unders": 0, "over_percentage": 0.0,
                "recent_overs": 0, "recent_unders": 0, "avg_total_points": 0.0,
            }
        
        # Get current injuries from DB
        canonical_injuries = await normalizer.get_current_injuries(team_name, sport, season)
        injuries_updated_at = None
        injuries_freshness_hours = float('inf')
        previous_injuries = None
        
        if canonical_injuries:
            from sqlalchemy import text
            result = await self.db.execute(
                text("""
                    SELECT updated_at FROM injury_current
                    WHERE team_name = :team_name AND sport = :sport AND season = :season
                """),
                {"team_name": team_name, "sport": sport, "season": season}
            )
            row = result.fetchone()
            if row:
                injuries_updated_at = row[0]
                injuries_freshness_hours = (datetime.now(timezone.utc) - injuries_updated_at).total_seconds() / 3600.0
            source_flags.append("db")
            
            # Get previous snapshot for trend detection
            previous_snapshot = await snapshot_manager.get_latest_injury_snapshot(
                team_name, sport, season
            )
            if previous_snapshot:
                # Normalize previous snapshot for comparison
                capability = get_sport_capability(sport)
                previous_injuries = await normalizer.normalize_and_update_injuries(
                    team_name, sport, season, previous_snapshot
                )
        else:
            # No injuries in DB - check if we should fetch
            if fallback_manager.should_fetch_injuries(0.0, context, data_missing=True):
                try:
                    raw_injuries = await self.get_injury_report(team_name, sport)
                    if raw_injuries:
                        # Save snapshot
                        await snapshot_manager.save_injury_snapshot(
                            team_name, sport, season, "api_espn", raw_injuries
                        )
                        # Normalize and update current
                        canonical_injuries = await normalizer.normalize_and_update_injuries(
                            team_name, sport, season, raw_injuries
                        )
                        injuries_updated_at = datetime.now(timezone.utc)
                        injuries_freshness_hours = 0.0
                        source_flags.append("api_espn")
                except Exception as e:
                    print(f"[StatsScraper] Error fetching injuries for {team_name}: {e}")
        
        # Default empty injuries if still None
        if not canonical_injuries:
            canonical_injuries = {
                "unit_counts": {},
                "impact_scores": {"offense_impact": 0.0, "defense_impact": 0.0, "overall_impact": 0.0, "uncertainty": 1.0},
                "trend": "stable",
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        
        # Build injury features
        canonical_injuries = injury_feature_builder.build_impact_scores(
            canonical_injuries, sport, previous_injuries
        )
        
        # Build team features
        derived_features = await team_feature_builder.build_features(
            team_name, sport, season, canonical_stats
        )
        
        # Calculate data quality
        data_quality = data_quality_scorer.calculate_quality(
            updated_at=stats_updated_at or injuries_updated_at or datetime.now(timezone.utc),
            canonical_stats=canonical_stats,
            canonical_injuries=canonical_injuries,
            sources_used=source_flags,
        )
        
        # Update team_features_current
        from sqlalchemy import text
        await self.db.execute(
            text("""
                INSERT INTO team_features_current
                (team_name, sport, season, updated_at, features_json, data_quality_json)
                VALUES
                (:team_name, :sport, :season, :updated_at, :features_json, :data_quality_json)
                ON CONFLICT (team_name, sport, season)
                DO UPDATE SET
                    updated_at = :updated_at,
                    features_json = :features_json,
                    data_quality_json = :data_quality_json
            """),
            {
                "team_name": team_name,
                "sport": sport,
                "season": season,
                "updated_at": datetime.now(timezone.utc),
                "features_json": derived_features,
                "data_quality_json": data_quality,
            }
        )
        await self.db.flush()
        
        return {
            "canonical_stats": canonical_stats,
            "injury_json": canonical_injuries,
            "derived_features": derived_features,
            "data_quality": data_quality,
            "source_flags": source_flags,
        }
    
    async def get_weather_data(
        self,
        city: str,
        state: str,
        game_time: datetime
    ) -> Optional[Dict]:
        """
        Get weather data for outdoor games (NFL, MLB)
        
        Returns dict with:
        - temperature
        - conditions (rain, snow, wind, etc.)
        - wind_speed
        - precipitation_probability
        - impact_assessment (how weather affects the game)
        """
        if not self.weather_api_key:
            return None
        
        cache_key = f"weather:{city}:{state}:{game_time.date()}"
        
        # Check cache
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 7200:  # 2 hour cache for weather
                return data
        
        try:
            # Use OpenWeatherMap API (free tier: 1000 calls/day)
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get lat/lon from city name (simplified - in production use geocoding)
                # For now, use a simple mapping or geocoding API
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "q": f"{city},{state},US",
                        "appid": self.weather_api_key,
                        "units": "imperial"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    weather_dict = {
                        "temperature": data.get("main", {}).get("temp"),
                        "feels_like": data.get("main", {}).get("feels_like"),
                        "conditions": data.get("weather", [{}])[0].get("main", "").lower(),
                        "description": data.get("weather", [{}])[0].get("description", ""),
                        "wind_speed": data.get("wind", {}).get("speed", 0),
                        "wind_direction": data.get("wind", {}).get("deg", 0),
                        "humidity": data.get("main", {}).get("humidity"),
                        "precipitation_probability": 0,  # Not in current weather API
                        "impact_assessment": self._assess_weather_impact(data),
                    }
                    
                    # Cache it
                    self._cache[cache_key] = (weather_dict, datetime.now())
                    return weather_dict
        except Exception as e:
            print(f"[StatsScraper] Weather fetch error: {e}")
        
        return None
    
    def _assess_weather_impact_from_data(self, weather_data: Dict) -> str:
        """Assess weather impact from weather fetcher data"""
        impacts = []
        temp = weather_data.get("temperature", 70)
        wind_speed = weather_data.get("wind_speed", 0)
        condition = weather_data.get("condition", "clear").lower()
        precipitation = weather_data.get("precipitation", 0)
        
        if condition in ["rain", "snow", "thunderstorm"]:
            impacts.append(f"{condition.capitalize()} conditions will significantly impact passing and ball handling")
        elif precipitation > 0:
            impacts.append(f"Precipitation expected, which may affect field conditions and passing accuracy")
        
        if wind_speed > 20:
            impacts.append(f"Strong winds ({wind_speed} mph) will heavily impact deep passing and field goal attempts")
        elif wind_speed > 15:
            impacts.append(f"Moderate to strong winds ({wind_speed} mph) may affect deep passes and kicking game")
        elif wind_speed > 10:
            impacts.append(f"Moderate winds ({wind_speed} mph) may slightly impact deep passes")
        
        if temp < 32:
            impacts.append("Freezing temperatures may affect ball handling and player performance")
        elif temp > 85:
            impacts.append("Hot conditions may lead to fatigue in later quarters")
        
        return ". ".join(impacts) if impacts else "Weather conditions should not significantly impact gameplay"
    
    def _assess_weather_impact(self, weather_data: Dict) -> str:
        """Assess how weather conditions might impact the game"""
        conditions = weather_data.get("weather", [{}])[0].get("main", "").lower()
        wind_speed = weather_data.get("wind", {}).get("speed", 0)
        temp = weather_data.get("main", {}).get("temp", 70)
        
        impacts = []
        
        if conditions in ["rain", "drizzle"]:
            impacts.append("Wet conditions favor running game and may reduce passing efficiency")
        elif conditions in ["snow"]:
            impacts.append("Snow significantly impacts passing and kicking games")
        
        if wind_speed > 15:
            impacts.append(f"Strong winds ({wind_speed} mph) will affect passing and kicking")
        elif wind_speed > 10:
            impacts.append(f"Moderate winds ({wind_speed} mph) may slightly impact deep passes")
        
        if temp < 32:
            impacts.append("Freezing temperatures may affect ball handling and player performance")
        elif temp > 85:
            impacts.append("Hot conditions may lead to fatigue in later quarters")
        
        return ". ".join(impacts) if impacts else "Weather conditions should not significantly impact gameplay"
    
    async def get_injury_report(
        self,
        team_name: str,
        league: str
    ) -> Optional[Dict]:
        """
        Get injury report for a team. Tries API-Sports cache (DB) first, then ESPN.
        Returns dict with: key_players_out, injury_summary, impact_assessment, total_injured, unit_counts.
        """
        cache_key = f"injuries:{team_name}:{league}"
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < 1800:
                return data

        try:
            sport_code_map = {
                "NFL": "nfl",
                "NBA": "nba",
                "NHL": "nhl",
                "MLB": "mlb",
                "EPL": "epl",
                "LALIGA": "laliga",
                "MLS": "mls",
                "UCL": "ucl",
                "SERIEA": "seriea",
                "BUNDESLIGA": "bundesliga",
                "SOCCER": "soccer",
            }
            sport_code = sport_code_map.get(league.upper())

            # 1) Try API-Sports cached injuries (DB) first
            sport_key = LEAGUE_TO_SPORT_KEY.get(league.upper())
            if sport_key:
                team_id = self._team_mapper.get_team_id(team_name, sport_key)
                if team_id is not None:
                    repo = ApisportsInjuryRepository(self.db)
                    row = await repo.get_latest_for_team(sport_key, team_id)
                    if row and getattr(row, "payload_json", None):
                        ttl = getattr(settings, "apisports_ttl_injuries_seconds", 21600)
                        if ApisportsInjuryRepository.is_fresh(
                            getattr(row, "last_fetched_at", None),
                            getattr(row, "stale_after_seconds", None) or ttl,
                        ):
                            canonical = apisports_injury_payload_to_canonical(
                                row.payload_json, league
                            )
                            canonical.setdefault("unit_counts", {})
                            self._cache[cache_key] = (canonical, datetime.now())
                            return canonical

            if not sport_code:
                injury_dict = {
                    "key_players_out": [],
                    "injury_summary": f"Injury data not available for {league}.",
                    "impact_assessment": "Unable to assess injury impact without current data.",
                    "total_injured": 0,
                    "unit_counts": {},
                }
                self._cache[cache_key] = (injury_dict, datetime.now())
                return injury_dict

            # 2) Fallback to ESPN via team-ID resolver (no team_abbr required)
            injury_data = None
            try:
                from app.services.espn.espn_team_resolver import EspnTeamResolver
                from app.services.espn.espn_injuries_client import EspnInjuriesClient
                resolver = EspnTeamResolver()
                client = EspnInjuriesClient()
                team_ref = await resolver.resolve_team_ref(sport_code, team_name)
                if team_ref:
                    injury_data = await client.fetch_injuries_for_team_ref(sport_code, team_ref)
            except Exception as e:
                print(f"[StatsScraper] ESPN injury fetch failed for {team_name}: {e}")

            if injury_data:
                key_players = injury_data.get("key_players_out", [])
                total_injured = injury_data.get("total_injured", injury_data.get("total_players_injured", 0))
                severity_score = injury_data.get("injury_severity_score", 0.0)
                if key_players:
                    player_names = [p.get("name", "Unknown") for p in key_players[:5]]
                    injury_summary = (
                        f"{len(key_players)} key players out: {', '.join(player_names)}, and {len(key_players) - 5} more."
                        if len(key_players) > 5
                        else f"Key players out: {', '.join(player_names)}."
                    )
                elif total_injured > 0:
                    injury_summary = f"{total_injured} player(s) listed on injury report."
                else:
                    injury_summary = "No significant injuries reported."
                if severity_score >= 0.7:
                    impact_assessment = "High injury impact. Key players missing may significantly affect performance."
                elif severity_score >= 0.4:
                    impact_assessment = "Moderate injury impact. Some key players out may affect performance."
                elif severity_score > 0:
                    impact_assessment = "Low injury impact. Minor injuries unlikely to significantly affect performance."
                else:
                    impact_assessment = "No significant injury concerns. Team is relatively healthy."
                injury_dict = {
                    "key_players_out": key_players,
                    "injury_summary": injury_summary,
                    "impact_assessment": impact_assessment,
                    "injury_severity_score": severity_score,
                    "total_injured": total_injured,
                    "unit_counts": injury_data.get("unit_counts", {}),
                }
            else:
                injury_dict = {
                    "key_players_out": [],
                    "injury_summary": "Injury data not currently available. Check official team sources for latest updates.",
                    "impact_assessment": "Unable to assess injury impact without current data.",
                    "injury_severity_score": 0.0,
                    "total_injured": 0,
                    "unit_counts": {},
                }

            self._cache[cache_key] = (injury_dict, datetime.now())
            return injury_dict

        except Exception as e:
            print(f"[StatsScraper] Error fetching injury report for {team_name} ({league}): {e}")
            import traceback
            traceback.print_exc()
            injury_dict = {
                "key_players_out": [],
                "injury_summary": f"Error fetching injury data: {str(e)}",
                "impact_assessment": "Unable to assess injury impact due to data fetch error.",
                "total_injured": 0,
                "unit_counts": {},
            }
            self._cache[cache_key] = (injury_dict, datetime.now())
            return injury_dict
    
    async def get_matchup_data(
        self,
        home_team: str,
        away_team: str,
        league: str,
        season: str,
        game_time: datetime
    ) -> Dict:
        """
        Get comprehensive matchup data for both teams.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            league: League code (NFL, NBA, NHL, MLB, etc.)
            season: Season year as string (e.g., "2024")
            game_time: Game start time
        
        Returns dict with:
        - home_team_stats
        - away_team_stats
        - head_to_head (if available)
        - weather (if outdoor game)
        - injuries (both teams)
        """
        # Get stats for both teams in parallel (try database first, then external APIs)
        # Always bypass cache to ensure fresh data for matchup analysis
        home_stats_task = self.get_team_stats(home_team, season, bypass_cache=True)
        away_stats_task = self.get_team_stats(away_team, season, bypass_cache=True)
        home_stats, away_stats = await asyncio.gather(home_stats_task, away_stats_task, return_exceptions=True)
        
        # Handle exceptions
        if isinstance(home_stats, Exception):
            print(f"[StatsScraper] Error fetching home stats: {home_stats}")
            home_stats = None
        if isinstance(away_stats, Exception):
            print(f"[StatsScraper] Error fetching away stats: {away_stats}")
            away_stats = None
        
        # If stats not in database, fetch from API-Sports/ESPN
        if not home_stats or not away_stats:
            try:
                # Map league to sport code
                league_to_sport = {
                    "NFL": "americanfootball_nfl",
                    "NBA": "basketball_nba",
                    "NHL": "icehockey_nhl",
                    "MLB": "baseball_mlb",
                    "EPL": "football",
                    "LALIGA": "football",
                    "MLS": "football",
                    "UCL": "football",
                    "SOCCER": "football",
                }
                
                sport_code_map = {
                    "NFL": "nfl",
                    "NBA": "nba",
                    "NHL": "nhl",
                    "MLB": "mlb",
                    "EPL": "epl",
                    "LALIGA": "laliga",
                    "MLS": "mls",
                    "UCL": "ucl",
                    "SOCCER": "soccer",
                }
                
                sport_key = league_to_sport.get(league.upper())
                sport_code = sport_code_map.get(league.upper())
                
                if sport_key:
                    espn = ESPNScraper()
                    
                    if not home_stats:
                        print(f"[StatsScraper] Fetching external stats for {home_team} from {sport_code}")
                        # Try API-Sports first
                        home_team_id = self._team_mapper.get_team_id(home_team, sport_key)
                        external_home = None
                        
                        if home_team_id:
                            try:
                                team_stat = await self._apisports_repo.get_team_stats(sport_key, home_team_id)
                                if team_stat and team_stat.payload_json:
                                    external_home = self._data_adapter.team_stats_to_internal_format(
                                        team_stat.payload_json,
                                        home_team_id,
                                        sport_key,
                                        team_stat.season
                                    )
                                    print(f"[StatsScraper] Successfully fetched API-Sports stats for {home_team}")
                            except Exception as e:
                                print(f"[StatsScraper] API-Sports failed for {home_team}: {e}")
                        
                        # Fallback to ESPN
                        if not external_home:
                            external_home = await espn.scrape_team_stats(home_team, sport_code)
                        
                        if external_home:
                            # Convert to internal format if needed
                            if 'strength_ratings' in external_home:
                                # Already in API-Sports format, use as-is
                                home_stats = external_home
                            else:
                                # ESPN format, convert
                                home_stats = self._convert_external_stats(external_home, home_team, season, None)
                            # Store in database for future use
                            await self._store_team_stats_in_db(home_stats)
                        else:
                            print(f"[StatsScraper] Failed to fetch external stats for {home_team} from both sources. Using zeroed defaults.")
                            home_stats = self._zero_stats(home_team, season, None)
                    
                    if not away_stats:
                        print(f"[StatsScraper] Fetching external stats for {away_team} from {sport_code}")
                        # Try API-Sports first
                        away_team_id = self._team_mapper.get_team_id(away_team, sport_key)
                        external_away = None
                        
                        if away_team_id:
                            try:
                                team_stat = await self._apisports_repo.get_team_stats(sport_key, away_team_id)
                                if team_stat and team_stat.payload_json:
                                    external_away = self._data_adapter.team_stats_to_internal_format(
                                        team_stat.payload_json,
                                        away_team_id,
                                        sport_key,
                                        team_stat.season
                                    )
                                    print(f"[StatsScraper] Successfully fetched API-Sports stats for {away_team}")
                            except Exception as e:
                                print(f"[StatsScraper] API-Sports failed for {away_team}: {e}")
                        
                        # Fallback to ESPN
                        if not external_away:
                            external_away = await espn.scrape_team_stats(away_team, sport_code)
                        
                        if external_away:
                            # Convert to internal format if needed
                            if 'strength_ratings' in external_away:
                                # Already in API-Sports format, use as-is
                                away_stats = external_away
                            else:
                                # ESPN format, convert
                                away_stats = self._convert_external_stats(external_away, away_team, season, None)
                            # Store in database for future use
                            await self._store_team_stats_in_db(away_stats)
                        else:
                            print(f"[StatsScraper] Failed to fetch external stats for {away_team} from both sources. Using zeroed defaults.")
                            away_stats = self._zero_stats(away_team, season, None)
            except Exception as e:
                print(f"[StatsScraper] Error fetching external stats: {e}")
                import traceback
                traceback.print_exc()
        
        # If still missing, provide zeroed stats to avoid 'not available'
        if not home_stats:
            print(f"[StatsScraper] Stats missing for {home_team}, using zeroed defaults")
            home_stats = self._zero_stats(home_team, season, None)
        if not away_stats:
            print(f"[StatsScraper] Stats missing for {away_team}, using zeroed defaults")
            away_stats = self._zero_stats(away_team, season, None)
        
        # Get weather and injuries in parallel
        weather_task = None
        if league in ["NFL", "MLB"]:
            async def _fetch_weather():
                try:
                    from app.services.data_fetchers.weather import WeatherFetcher
                    weather_fetcher = WeatherFetcher()
                    weather_data = await weather_fetcher.get_game_weather(
                        home_team=home_team,
                        game_time=game_time
                    )
                    if weather_data:
                        return {
                            "temperature": weather_data.get("temperature", 0),
                            "feels_like": weather_data.get("feels_like", 0),
                            "description": weather_data.get("description", weather_data.get("condition", "clear")),
                            "wind_speed": weather_data.get("wind_speed", 0),
                            "wind_direction": weather_data.get("wind_direction", 0),
                            "humidity": weather_data.get("humidity", 0),
                            "precipitation": weather_data.get("precipitation", 0),
                            "condition": weather_data.get("condition", "clear"),
                            "is_outdoor": weather_data.get("is_outdoor", True),
                            "affects_game": weather_data.get("affects_game", False),
                            "impact_assessment": self._assess_weather_impact_from_data(weather_data)
                        }
                except Exception as e:
                    print(f"[StatsScraper] Error fetching weather: {e}")
                    return None
            weather_task = _fetch_weather()
        
        # Get injuries in parallel
        home_injuries_task = self.get_injury_report(home_team, league)
        away_injuries_task = self.get_injury_report(away_team, league)
        
        # Gather all parallel tasks
        tasks = [home_injuries_task, away_injuries_task]
        if weather_task:
            tasks.append(weather_task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        home_injuries = results[0] if not isinstance(results[0], Exception) else None
        away_injuries = results[1] if not isinstance(results[1], Exception) else None
        weather = results[2] if len(results) > 2 and not isinstance(results[2], Exception) else None

        # If stats are still missing, provide zeroed structures to avoid "not available" text
        if not home_stats:
            print(f"[StatsScraper] WARNING: Missing stats for {home_team}, returning zeroed stats")
            home_stats = self._zero_stats(home_team, season)
        if not away_stats:
            print(f"[StatsScraper] WARNING: Missing stats for {away_team}, returning zeroed stats")
            away_stats = self._zero_stats(away_team, season)
        
        return {
            "home_team_stats": home_stats,
            "away_team_stats": away_stats,
            "weather": weather,
            "home_injuries": home_injuries,
            "away_injuries": away_injuries,
            "head_to_head": None,  # Can be added later from game results
        }
    
    def clear_cache(self):
        """Clear the in-memory cache"""
        self._cache.clear()

    def _zero_stats(self, team_name: str, season: str, week: Optional[int] = None) -> Dict:
        """Return a zeroed stats structure to keep the formatter from showing 'not available'."""
        return {
            "team_name": team_name,
            "season": season,
            "week": week,
            "record": {
                "wins": 0,
                "losses": 0,
                "ties": 0,
                "win_percentage": 0.0,
            },
            "offense": {
                "points_per_game": 0.0,
                "yards_per_game": 0.0,
                "passing_yards_per_game": 0.0,
                "rushing_yards_per_game": 0.0,
            },
            "defense": {
                "points_allowed_per_game": 0.0,
                "yards_allowed_per_game": 0.0,
                "turnovers_forced": 0,
            },
            "recent_form": {
                "recent_wins": 0,
                "recent_losses": 0,
                "home_record": "0-0",
                "away_record": "0-0",
            },
            "strength_ratings": {
                "offensive_rating": 0.0,
                "defensive_rating": 0.0,
                "overall_rating": 0.0,
            },
            "ats_trends": {
                "wins": 0,
                "losses": 0,
                "pushes": 0,
                "win_percentage": 0.0,
                "recent": "0-0",
                "home": "0-0",
                "away": "0-0",
            },
            "over_under_trends": {
                "overs": 0,
                "unders": 0,
                "over_percentage": 0.0,
                "recent_overs": 0,
                "recent_unders": 0,
                "avg_total_points": 0.0,
            },
        }
    
    async def get_team_bundle(
        self,
        team_name: str,
        sport: str,
        season: str,
        context: FetchContext,
    ) -> Dict:
        """
        Get comprehensive team data bundle using stats platform v2.
        
        Returns:
            {
                "canonical_stats": Dict,
                "injury_json": Dict,
                "derived_features": Dict,
                "data_quality": Dict,
                "source_flags": List[str],
            }
        """
        # Initialize services
        snapshot_manager = SnapshotManager(self.db)
        normalizer = StatsNormalizer(self.db)
        team_feature_builder = TeamFeatureBuilder(self.db)
        injury_feature_builder = InjuryFeatureBuilder()
        data_quality_scorer = DataQualityScorer()
        fallback_manager = FallbackManager()
        
        # Determine season mode if not provided
        if context.season_mode is None:
            context.season_mode = get_season_mode(sport, datetime.now(timezone.utc))
        
        source_flags = []
        
        # Try to get current stats from DB
        canonical_stats = await normalizer.get_current_stats(team_name, sport, season)
        stats_updated_at = None
        stats_freshness_hours = float('inf')
        
        if canonical_stats:
            # Get updated_at from DB
            from sqlalchemy import text
            result = await self.db.execute(
                text("""
                    SELECT updated_at FROM team_stats_current
                    WHERE team_name = :team_name AND sport = :sport AND season = :season
                """),
                {"team_name": team_name, "sport": sport, "season": season}
            )
            row = result.fetchone()
            if row:
                stats_updated_at = row[0]
                stats_freshness_hours = (datetime.now(timezone.utc) - stats_updated_at).total_seconds() / 3600.0
            source_flags.append("db")
        else:
            # No stats in DB - check if we should fetch
            if fallback_manager.should_fetch_stats(0.0, context, data_missing=True):
                # Fetch from external API
                try:
                    raw_stats = await self.get_team_stats(team_name, season)
                    if raw_stats:
                        # Save snapshot
                        await snapshot_manager.save_stats_snapshot(
                            team_name, sport, season, "api_espn", raw_stats
                        )
                        # Normalize and update current
                        canonical_stats = await normalizer.normalize_and_update_stats(
                            team_name, sport, season, raw_stats
                        )
                        stats_updated_at = datetime.now(timezone.utc)
                        stats_freshness_hours = 0.0
                        source_flags.append("api_espn")
                except Exception as e:
                    print(f"[StatsScraper] Error fetching stats for {team_name}: {e}")
        
        # If still no stats and off-season, try last completed season
        if not canonical_stats and context.season_mode == SeasonMode.OFF_SEASON:
            from app.services.sports.sport_registry import get_last_completed_season
            last_season = get_last_completed_season(sport, datetime.now(timezone.utc))
            if last_season:
                canonical_stats = await normalizer.get_current_stats(team_name, sport, last_season)
                if canonical_stats:
                    source_flags.append("db_last_season")
        
        # Default empty stats if still None
        if not canonical_stats:
            canonical_stats = {}

        # Merge ATS/OU from legacy team_stats table so v2 bundle matches what CoreAnalysisGenerator._build_trends expects
        ats_ou = await self._get_ats_ou_from_legacy(team_name, season)
        if ats_ou:
            canonical_stats["ats_trends"] = ats_ou["ats_trends"]
            canonical_stats["over_under_trends"] = ats_ou["over_under_trends"]
        elif "ats_trends" not in canonical_stats:
            canonical_stats["ats_trends"] = {
                "wins": 0, "losses": 0, "pushes": 0, "win_percentage": 0.0,
                "recent": "0-0", "home": "0-0", "away": "0-0",
            }
        if "over_under_trends" not in canonical_stats:
            canonical_stats["over_under_trends"] = {
                "overs": 0, "unders": 0, "over_percentage": 0.0,
                "recent_overs": 0, "recent_unders": 0, "avg_total_points": 0.0,
            }
        
        # Get current injuries from DB
        canonical_injuries = await normalizer.get_current_injuries(team_name, sport, season)
        injuries_updated_at = None
        injuries_freshness_hours = float('inf')
        previous_injuries = None
        
        if canonical_injuries:
            from sqlalchemy import text
            result = await self.db.execute(
                text("""
                    SELECT updated_at FROM injury_current
                    WHERE team_name = :team_name AND sport = :sport AND season = :season
                """),
                {"team_name": team_name, "sport": sport, "season": season}
            )
            row = result.fetchone()
            if row:
                injuries_updated_at = row[0]
                injuries_freshness_hours = (datetime.now(timezone.utc) - injuries_updated_at).total_seconds() / 3600.0
            source_flags.append("db")
            
            # Get previous snapshot for trend detection
            previous_snapshot = await snapshot_manager.get_latest_injury_snapshot(
                team_name, sport, season
            )
            if previous_snapshot:
                # Normalize previous snapshot for comparison
                capability = get_sport_capability(sport)
                previous_injuries = await normalizer.normalize_and_update_injuries(
                    team_name, sport, season, previous_snapshot
                )
        else:
            # No injuries in DB - check if we should fetch
            if fallback_manager.should_fetch_injuries(0.0, context, data_missing=True):
                try:
                    raw_injuries = await self.get_injury_report(team_name, sport)
                    if raw_injuries:
                        # Save snapshot
                        await snapshot_manager.save_injury_snapshot(
                            team_name, sport, season, "api_espn", raw_injuries
                        )
                        # Normalize and update current
                        canonical_injuries = await normalizer.normalize_and_update_injuries(
                            team_name, sport, season, raw_injuries
                        )
                        injuries_updated_at = datetime.now(timezone.utc)
                        injuries_freshness_hours = 0.0
                        source_flags.append("api_espn")
                except Exception as e:
                    print(f"[StatsScraper] Error fetching injuries for {team_name}: {e}")
        
        # Default empty injuries if still None
        if not canonical_injuries:
            canonical_injuries = {
                "unit_counts": {},
                "impact_scores": {"offense_impact": 0.0, "defense_impact": 0.0, "overall_impact": 0.0, "uncertainty": 1.0},
                "trend": "stable",
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        
        # Build injury features
        canonical_injuries = injury_feature_builder.build_impact_scores(
            canonical_injuries, sport, previous_injuries
        )
        
        # Build team features
        derived_features = await team_feature_builder.build_features(
            team_name, sport, season, canonical_stats
        )
        
        # Calculate data quality
        data_quality = data_quality_scorer.calculate_quality(
            updated_at=stats_updated_at or injuries_updated_at or datetime.now(timezone.utc),
            canonical_stats=canonical_stats,
            canonical_injuries=canonical_injuries,
            sources_used=source_flags,
        )
        
        # Update team_features_current
        from sqlalchemy import text
        await self.db.execute(
            text("""
                INSERT INTO team_features_current
                (team_name, sport, season, updated_at, features_json, data_quality_json)
                VALUES
                (:team_name, :sport, :season, :updated_at, :features_json, :data_quality_json)
                ON CONFLICT (team_name, sport, season)
                DO UPDATE SET
                    updated_at = :updated_at,
                    features_json = :features_json,
                    data_quality_json = :data_quality_json
            """),
            {
                "team_name": team_name,
                "sport": sport,
                "season": season,
                "updated_at": datetime.now(timezone.utc),
                "features_json": derived_features,
                "data_quality_json": data_quality,
            }
        )
        await self.db.flush()
        
        return {
            "canonical_stats": canonical_stats,
            "injury_json": canonical_injuries,
            "derived_features": derived_features,
            "data_quality": data_quality,
            "source_flags": source_flags,
        }

