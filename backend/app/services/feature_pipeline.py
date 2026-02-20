"""
Unified Matchup Feature Pipeline

Builds the "Parlay Gorilla Matchup Vector" by combining data from multiple sources:
- Odds API (implied probabilities, primary scheduling)
- API-Sports (stats, results, form, standings; scheduling fallback)
- ESPN (matchup context, backup stats)
- Weather (for outdoor sports)

Returns a standardized feature vector for all prediction models.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from datetime import datetime, date, timedelta
import logging
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

# Data fetchers
from app.services.data_fetchers.espn_scraper import get_espn_scraper, ESPNScraper
from app.services.data_fetchers.weather import WeatherFetcher
from app.services.data_fetchers.injuries import InjuryFetcher

# API-Sports integration
from app.repositories.sports_data_repository import SportsDataRepository
from app.services.apisports.team_mapper import get_team_mapper
from app.services.apisports.data_adapter import ApiSportsDataAdapter
from app.services.feature_builder_service import FeatureBuilderService

logger = logging.getLogger(__name__)


@dataclass
class MatchupFeatureVector:
    """
    Standardized feature vector for matchup predictions.
    
    Contains all features used by prediction models:
    - Offensive/defensive ratings
    - Situational factors (rest, travel, weather)
    - Market data (implied probabilities)
    - Recent form and momentum
    """
    # Team identifiers
    home_team: str
    away_team: str
    sport: str
    game_id: Optional[str] = None
    game_time: Optional[datetime] = None
    
    # Offensive ratings (0-100 scale)
    offense_rating_home: float = 50.0
    offense_rating_away: float = 50.0
    
    # Defensive ratings (0-100 scale, higher = better defense)
    defense_rating_home: float = 50.0
    defense_rating_away: float = 50.0
    
    # Pace/tempo (sport-specific, normalized)
    pace_home: float = 100.0  # 100 = league average
    pace_away: float = 100.0
    
    # Style matchup score (-1 to 1, positive favors home)
    style_matchup_score: float = 0.0
    
    # Home advantage factor (sport-specific default)
    home_advantage: float = 0.025  # 2.5% default
    
    # Rest and travel
    rest_days_home: int = 7
    rest_days_away: int = 7
    travel_distance_away: float = 0.0  # Miles
    is_back_to_back_home: bool = False
    is_back_to_back_away: bool = False
    
    # Weather impact (outdoor sports only)
    weather_impact: float = 0.0  # -0.1 to 0.1
    temperature: Optional[float] = None
    wind_speed: Optional[float] = None
    is_outdoor: bool = True
    
    # Injury severity (0-1 scale)
    injury_severity_home: float = 0.0
    injury_severity_away: float = 0.0
    key_players_out_home: List[str] = field(default_factory=list)
    key_players_out_away: List[str] = field(default_factory=list)
    
    # Recent form (win % in last 5 games)
    recent_form_home: float = 0.5
    recent_form_away: float = 0.5
    
    # ATS/totals trends
    ats_cover_rate_home: float = 0.5
    ats_cover_rate_away: float = 0.5
    over_rate_home: float = 0.5
    over_rate_away: float = 0.5
    
    # Market-implied probabilities (from odds)
    implied_prob_home: float = 0.5
    implied_prob_away: float = 0.5
    spread_line: Optional[float] = None
    total_line: Optional[float] = None
    
    # Head-to-head
    h2h_games: int = 0
    h2h_home_wins: int = 0
    h2h_edge: float = 0.0  # -1 to 1
    
    # Win percentages
    win_pct_home: float = 0.5
    win_pct_away: float = 0.5
    
    # Data quality flags
    has_odds_data: bool = False
    has_stats_data: bool = False
    has_injury_data: bool = False
    has_weather_data: bool = False
    data_quality_score: float = 0.0  # 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API responses"""
        return {
            'home_team': self.home_team,
            'away_team': self.away_team,
            'sport': self.sport,
            'game_id': self.game_id,
            'game_time': self.game_time.isoformat() if self.game_time else None,
            
            'offense_rating_home': self.offense_rating_home,
            'offense_rating_away': self.offense_rating_away,
            'defense_rating_home': self.defense_rating_home,
            'defense_rating_away': self.defense_rating_away,
            
            'pace_home': self.pace_home,
            'pace_away': self.pace_away,
            'style_matchup_score': self.style_matchup_score,
            'home_advantage': self.home_advantage,
            
            'rest_days_home': self.rest_days_home,
            'rest_days_away': self.rest_days_away,
            'travel_distance_away': self.travel_distance_away,
            'is_back_to_back_home': self.is_back_to_back_home,
            'is_back_to_back_away': self.is_back_to_back_away,
            
            'weather_impact': self.weather_impact,
            'temperature': self.temperature,
            'wind_speed': self.wind_speed,
            'is_outdoor': self.is_outdoor,
            
            'injury_severity_home': self.injury_severity_home,
            'injury_severity_away': self.injury_severity_away,
            'key_players_out_home': self.key_players_out_home,
            'key_players_out_away': self.key_players_out_away,
            
            'recent_form_home': self.recent_form_home,
            'recent_form_away': self.recent_form_away,
            
            'ats_cover_rate_home': self.ats_cover_rate_home,
            'ats_cover_rate_away': self.ats_cover_rate_away,
            'over_rate_home': self.over_rate_home,
            'over_rate_away': self.over_rate_away,
            
            'implied_prob_home': self.implied_prob_home,
            'implied_prob_away': self.implied_prob_away,
            'spread_line': self.spread_line,
            'total_line': self.total_line,
            
            'h2h_games': self.h2h_games,
            'h2h_home_wins': self.h2h_home_wins,
            'h2h_edge': self.h2h_edge,
            
            'win_pct_home': self.win_pct_home,
            'win_pct_away': self.win_pct_away,
            
            'has_odds_data': self.has_odds_data,
            'has_stats_data': self.has_stats_data,
            'has_injury_data': self.has_injury_data,
            'has_weather_data': self.has_weather_data,
            'data_quality_score': self.data_quality_score,
        }


# Sport-specific home advantage values
HOME_ADVANTAGE_BY_SPORT = {
    'nfl': 0.025,  # 2.5%
    'americanfootball_nfl': 0.025,
    'nba': 0.035,  # 3.5%
    'basketball_nba': 0.035,
    'wnba': 0.033,  # 3.3%
    'basketball_wnba': 0.033,
    'nhl': 0.025,  # 2.5%
    'icehockey_nhl': 0.025,
    'mlb': 0.020,  # 2.0%
    'baseball_mlb': 0.020,
    'soccer': 0.030,  # 3.0%
    'soccer_epl': 0.030,
    'soccer_mls': 0.025,
}


class FeaturePipeline:
    """
    Unified feature pipeline that combines data from multiple sources
    to build the Parlay Gorilla Matchup Vector.
    """
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        
        # Initialize API-Sports services
        if db:
            self._apisports_repo = SportsDataRepository(db)
            self._feature_builder = FeatureBuilderService(db)
        else:
            self._apisports_repo = None
            self._feature_builder = None
        
        self._team_mapper = get_team_mapper()
        self._data_adapter = ApiSportsDataAdapter()
        
        # Initialize other fetchers (created on demand)
        self._espn_scraper: Optional[ESPNScraper] = None
        self._weather_fetcher: Optional[WeatherFetcher] = None
        self._injury_fetcher: Optional[InjuryFetcher] = None
    
    def _get_espn_scraper(self) -> ESPNScraper:
        """Get or create ESPN scraper"""
        if self._espn_scraper is None:
            self._espn_scraper = get_espn_scraper()
        return self._espn_scraper
    
    def _get_weather_fetcher(self) -> WeatherFetcher:
        """Get or create weather fetcher"""
        if self._weather_fetcher is None:
            self._weather_fetcher = WeatherFetcher()
        return self._weather_fetcher
    
    def _get_injury_fetcher(self) -> InjuryFetcher:
        """Get or create injury fetcher"""
        if self._injury_fetcher is None:
            self._injury_fetcher = InjuryFetcher()
        return self._injury_fetcher
    
    async def build_matchup_features(
        self,
        home_team: str,
        away_team: str,
        sport: str,
        game_id: Optional[str] = None,
        game_time: Optional[datetime] = None,
        odds_data: Optional[Dict] = None,
    ) -> MatchupFeatureVector:
        """
        Build the complete matchup feature vector by combining all data sources.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            sport: Sport code (nfl, nba, etc.)
            game_id: Optional game ID
            game_time: Optional game start time
            odds_data: Optional pre-fetched odds data
        
        Returns:
            MatchupFeatureVector with all available features
        """
        logger.info(f"[FeaturePipeline] Building features for {away_team} @ {home_team} ({sport})")
        
        # Initialize feature vector with defaults
        features = MatchupFeatureVector(
            home_team=home_team,
            away_team=away_team,
            sport=sport.upper(),
            game_id=game_id,
            game_time=game_time,
            home_advantage=HOME_ADVANTAGE_BY_SPORT.get(sport.lower(), 0.025),
        )
        
        # Fetch data from all sources in parallel
        tasks = [
            self._fetch_team_stats(home_team, away_team, sport),
            self._fetch_injuries(home_team, away_team, sport),
            self._fetch_recent_form(home_team, away_team, sport),
            self._fetch_matchup_context(home_team, away_team, sport),
        ]
        
        # Add weather fetch for outdoor sports
        if self._sport_supports_weather(sport) and game_time:
            tasks.append(self._fetch_weather(home_team, game_time, sport))
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process team stats
        if not isinstance(results[0], Exception) and isinstance(results[0], tuple):
            home_stats, away_stats = results[0]
            if home_stats or away_stats:
                self._apply_team_stats(features, home_stats, away_stats, sport)
                features.has_stats_data = True
        
        # Process injuries
        if len(results) > 1 and not isinstance(results[1], Exception) and isinstance(results[1], tuple):
            home_injuries, away_injuries = results[1]
            if home_injuries or away_injuries:
                self._apply_injuries(features, home_injuries, away_injuries)
                features.has_injury_data = True
        
        # Process recent form
        if len(results) > 2 and not isinstance(results[2], Exception) and results[2]:
            home_form, away_form = results[2]
            self._apply_recent_form(features, home_form, away_form)
        
        # Process matchup context
        if len(results) > 3 and not isinstance(results[3], Exception) and results[3]:
            context = results[3]
            self._apply_matchup_context(features, context)
        
        # Process weather (if applicable)
        if len(results) > 4 and not isinstance(results[4], Exception) and results[4]:
            weather = results[4]
            self._apply_weather(features, weather, sport)
            features.has_weather_data = True
        
        # Apply odds data if provided
        if odds_data:
            self._apply_odds_data(features, odds_data)
            features.has_odds_data = True
        
        # Calculate data quality score
        features.data_quality_score = self._calculate_data_quality(features)
        
        # Calculate style matchup score
        features.style_matchup_score = self._calculate_style_matchup(features, sport)
        
        logger.info(f"[FeaturePipeline] Features built with quality score: {features.data_quality_score:.1f}")
        
        return features
    
    async def _fetch_team_stats(
        self, 
        home_team: str, 
        away_team: str, 
        sport: str
    ) -> tuple[Optional[Dict], Optional[Dict]]:
        """Fetch team statistics from API-Sports with ESPN fallback"""
        if not self.db or not self._apisports_repo:
            # Fallback to ESPN if no DB session
            espn = self._get_espn_scraper()
            home_stats = await espn.scrape_team_stats(home_team, sport)
            away_stats = await espn.scrape_team_stats(away_team, sport)
            return home_stats, away_stats
        
        # Map team names to API-Sports team IDs
        sport_key = self._normalize_sport_key(sport)
        home_team_id = self._team_mapper.get_team_id(home_team, sport_key)
        away_team_id = self._team_mapper.get_team_id(away_team, sport_key)
        
        home_stats = None
        away_stats = None
        
        # Try API-Sports first
        if home_team_id:
            team_stat = await self._apisports_repo.get_team_stats(sport_key, home_team_id)
            if team_stat and team_stat.payload_json:
                home_stats = self._data_adapter.team_stats_to_internal_format(
                    team_stat.payload_json,
                    home_team_id,
                    sport_key,
                    team_stat.season
                )
        
        if away_team_id:
            team_stat = await self._apisports_repo.get_team_stats(sport_key, away_team_id)
            if team_stat and team_stat.payload_json:
                away_stats = self._data_adapter.team_stats_to_internal_format(
                    team_stat.payload_json,
                    away_team_id,
                    sport_key,
                    team_stat.season
                )
        
        # Fallback to ESPN if API-Sports data unavailable
        espn = self._get_espn_scraper()
        if not home_stats:
            home_stats = await espn.scrape_team_stats(home_team, sport)
        
        if not away_stats:
            away_stats = await espn.scrape_team_stats(away_team, sport)
        
        return home_stats, away_stats
    
    def _normalize_sport_key(self, sport: str) -> str:
        """Normalize sport identifier to API-Sports sport key."""
        sport_lower = sport.lower().strip()
        
        # Map to API-Sports keys
        sport_map = {
            "nfl": "americanfootball_nfl",
            "americanfootball_nfl": "americanfootball_nfl",
            "americanfootball": "americanfootball_nfl",
            "nba": "basketball_nba",
            "basketball_nba": "basketball_nba",
            "wnba": "basketball_wnba",
            "basketball_wnba": "basketball_wnba",
            "basketball": "basketball_nba",
            "nhl": "icehockey_nhl",
            "icehockey_nhl": "icehockey_nhl",
            "icehockey": "icehockey_nhl",
            "hockey": "icehockey_nhl",
            "mlb": "baseball_mlb",
            "baseball_mlb": "baseball_mlb",
            "baseball": "baseball_mlb",
            "soccer": "football",
            "football_soccer": "football",
            "epl": "football",
            "mls": "football",
            "laliga": "football",
            "la liga": "football",
        }
        
        return sport_map.get(sport_lower, sport_lower)

    def _sport_supports_weather(self, sport: str) -> bool:
        """True for outdoor leagues where weather is a meaningful input."""
        sport_lower = (sport or "").lower().strip()
        return sport_lower in {
            "nfl",
            "americanfootball_nfl",
            "mlb",
            "baseball_mlb",
            "soccer",
            "soccer_epl",
            "soccer_mls",
            "epl",
            "mls",
            "laliga",
            "la liga",
            "ucl",
            "seriea",
            "bundesliga",
        }
    
    async def _fetch_injuries(
        self, 
        home_team: str, 
        away_team: str, 
        sport: str
    ) -> tuple[Optional[Dict], Optional[Dict]]:
        """Fetch injury reports using sport-aware injury fetcher."""
        fetcher = self._get_injury_fetcher()
        fetcher.sport = (sport or "").lower().strip()

        home_raw, away_raw = await asyncio.gather(
            fetcher.get_team_injuries(home_team),
            fetcher.get_team_injuries(away_team),
        )

        return (
            self._injury_list_to_summary(home_raw),
            self._injury_list_to_summary(away_raw),
        )

    def _injury_list_to_summary(self, injuries: Optional[List[Dict]]) -> Optional[Dict]:
        if injuries is None:
            return None

        if not injuries:
            return {
                "key_players_out": [],
                "injury_severity_score": 0.0,
                "total_injured": 0,
            }

        severity = 0.0
        key_players_out: List[Dict[str, Any]] = []
        for injury in injuries[:20]:
            if not isinstance(injury, dict):
                continue
            status = str(injury.get("status", "")).lower()
            if any(token in status for token in ["out", "doubtful", "ir", "pup"]):
                severity += 0.2
            elif any(token in status for token in ["questionable", "limited"]):
                severity += 0.1
            elif any(token in status for token in ["probable"]):
                severity += 0.05

            key_players_out.append(
                {
                    "name": injury.get("player", ""),
                    "position": injury.get("position", ""),
                    "status": injury.get("status", ""),
                    "description": injury.get("injury", ""),
                }
            )

        return {
            "key_players_out": key_players_out,
            "injury_severity_score": min(1.0, severity),
            "total_injured": len(key_players_out),
        }
    
    async def _fetch_recent_form(
        self, 
        home_team: str, 
        away_team: str, 
        sport: str
    ) -> tuple[List[Dict], List[Dict]]:
        """Fetch recent game results from API-Sports FeatureBuilderService with ESPN fallback"""
        if not self.db or not self._feature_builder:
            # Fallback to ESPN if no DB session
            espn = self._get_espn_scraper()
            home_form = await espn.scrape_recent_games(home_team, sport, n=5)
            away_form = await espn.scrape_recent_games(away_team, sport, n=5)
            return home_form or [], away_form or []
        
        sport_key = self._normalize_sport_key(sport)
        home_team_id = self._team_mapper.get_team_id(home_team, sport_key)
        away_team_id = self._team_mapper.get_team_id(away_team, sport_key)
        
        home_form = []
        away_form = []
        
        # Try API-Sports FeatureBuilderService first
        if home_team_id:
            features = await self._feature_builder.build_team_features(
                sport=sport_key,
                team_id=home_team_id,
                last_n=5
            )
            if features:
                # Convert to form list format
                wins = features.get("last_n_form_wins", 0)
                losses = features.get("last_n_form_losses", 0)
                home_form = [{"result": "W"} for _ in range(wins)] + [{"result": "L"} for _ in range(losses)]
        
        if away_team_id:
            features = await self._feature_builder.build_team_features(
                sport=sport_key,
                team_id=away_team_id,
                last_n=5
            )
            if features:
                wins = features.get("last_n_form_wins", 0)
                losses = features.get("last_n_form_losses", 0)
                away_form = [{"result": "W"} for _ in range(wins)] + [{"result": "L"} for _ in range(losses)]
        
        # Fallback to ESPN if API-Sports data unavailable
        espn = self._get_espn_scraper()
        if not home_form:
            home_form = await espn.scrape_recent_games(home_team, sport, n=5)
        
        if not away_form:
            away_form = await espn.scrape_recent_games(away_team, sport, n=5)
        
        return home_form or [], away_form or []
    
    async def _fetch_matchup_context(
        self, 
        home_team: str, 
        away_team: str, 
        sport: str
    ) -> Optional[Dict]:
        """Fetch matchup context (H2H, storylines)"""
        espn = self._get_espn_scraper()
        return await espn.scrape_matchup_context(home_team, away_team, sport)
    
    async def _fetch_weather(
        self, 
        home_team: str, 
        game_time: datetime,
        sport: str
    ) -> Optional[Dict]:
        """Fetch weather data for outdoor games"""
        weather = self._get_weather_fetcher()
        return await weather.get_game_weather(home_team, game_time)
    
    def _apply_team_stats(
        self, 
        features: MatchupFeatureVector, 
        home_stats: Optional[Dict], 
        away_stats: Optional[Dict],
        sport: str
    ):
        """Apply team statistics to feature vector (supports both API-Sports and ESPN formats)"""
        if home_stats:
            # Check if it's API-Sports format (has strength_ratings) or ESPN format (has efficiency)
            if 'strength_ratings' in home_stats:
                # API-Sports format
                strength = home_stats.get('strength_ratings', {})
                features.offense_rating_home = strength.get('offensive_rating', 50.0)
                features.defense_rating_home = strength.get('defensive_rating', 50.0)
                
                record = home_stats.get('record', {})
                features.win_pct_home = record.get('win_percentage', 0.5)
            else:
                # ESPN/Sportsradar format (legacy)
                efficiency = home_stats.get('efficiency', {})
                features.offense_rating_home = efficiency.get('offensive_efficiency', 50.0)
                features.defense_rating_home = efficiency.get('defensive_efficiency', 50.0)
                
                record = home_stats.get('record', {})
                features.win_pct_home = record.get('win_percentage', 0.5)
            
            # Pace (for applicable sports)
            if sport.lower() in ['nba', 'basketball_nba', 'wnba', 'basketball_wnba']:
                if 'advanced' in home_stats:
                    advanced = home_stats.get('advanced', {})
                    features.pace_home = advanced.get('pace', 100.0)
                # API-Sports doesn't provide pace directly, keep default
        
        if away_stats:
            if 'strength_ratings' in away_stats:
                # API-Sports format
                strength = away_stats.get('strength_ratings', {})
                features.offense_rating_away = strength.get('offensive_rating', 50.0)
                features.defense_rating_away = strength.get('defensive_rating', 50.0)
                
                record = away_stats.get('record', {})
                features.win_pct_away = record.get('win_percentage', 0.5)
            else:
                # ESPN/Sportsradar format (legacy)
                efficiency = away_stats.get('efficiency', {})
                features.offense_rating_away = efficiency.get('offensive_efficiency', 50.0)
                features.defense_rating_away = efficiency.get('defensive_efficiency', 50.0)
                
                record = away_stats.get('record', {})
                features.win_pct_away = record.get('win_percentage', 0.5)
            
            if sport.lower() in ['nba', 'basketball_nba', 'wnba', 'basketball_wnba']:
                if 'advanced' in away_stats:
                    advanced = away_stats.get('advanced', {})
                    features.pace_away = advanced.get('pace', 100.0)
    
    def _apply_injuries(
        self, 
        features: MatchupFeatureVector, 
        home_injuries: Optional[Dict], 
        away_injuries: Optional[Dict]
    ):
        """Apply injury data to feature vector"""
        if home_injuries:
            features.injury_severity_home = home_injuries.get('injury_severity_score', 0.0)
            key_players = home_injuries.get('key_players_out', [])
            features.key_players_out_home = [
                p.get('name', '') if isinstance(p, dict) else str(p)
                for p in key_players
            ]
        
        if away_injuries:
            features.injury_severity_away = away_injuries.get('injury_severity_score', 0.0)
            key_players = away_injuries.get('key_players_out', [])
            features.key_players_out_away = [
                p.get('name', '') if isinstance(p, dict) else str(p)
                for p in key_players
            ]
    
    def _apply_recent_form(
        self, 
        features: MatchupFeatureVector, 
        home_form: List[Dict], 
        away_form: List[Dict]
    ):
        """Apply recent form data to feature vector"""
        if home_form:
            wins = sum(1 for g in home_form if g.get('result') == 'W' or g.get('is_win', False))
            features.recent_form_home = wins / len(home_form) if home_form else 0.5
            
            # Check for back-to-back
            if len(home_form) >= 1:
                last_game_date = home_form[0].get('date')
                if last_game_date and features.game_time:
                    try:
                        if isinstance(last_game_date, str):
                            last_game = datetime.fromisoformat(last_game_date.replace('Z', '+00:00'))
                        else:
                            last_game = last_game_date
                        days_rest = (features.game_time - last_game).days
                        features.rest_days_home = max(1, days_rest)
                        features.is_back_to_back_home = days_rest <= 1
                    except (ValueError, TypeError):
                        pass
        
        if away_form:
            wins = sum(1 for g in away_form if g.get('result') == 'W' or g.get('is_win', False))
            features.recent_form_away = wins / len(away_form) if away_form else 0.5
            
            if len(away_form) >= 1:
                last_game_date = away_form[0].get('date')
                if last_game_date and features.game_time:
                    try:
                        if isinstance(last_game_date, str):
                            last_game = datetime.fromisoformat(last_game_date.replace('Z', '+00:00'))
                        else:
                            last_game = last_game_date
                        days_rest = (features.game_time - last_game).days
                        features.rest_days_away = max(1, days_rest)
                        features.is_back_to_back_away = days_rest <= 1
                    except (ValueError, TypeError):
                        pass
    
    def _apply_matchup_context(
        self, 
        features: MatchupFeatureVector, 
        context: Optional[Dict]
    ):
        """Apply matchup context to feature vector"""
        if not context:
            return
        
        h2h = context.get('head_to_head', {})
        features.h2h_games = h2h.get('games', 0)
        features.h2h_home_wins = h2h.get('home_team_wins', 0)
        
        if features.h2h_games > 0:
            features.h2h_edge = (features.h2h_home_wins - (features.h2h_games - features.h2h_home_wins)) / features.h2h_games
    
    def _apply_weather(
        self, 
        features: MatchupFeatureVector, 
        weather: Optional[Dict],
        sport: str
    ):
        """Apply weather data to feature vector"""
        if not weather:
            return
        
        features.is_outdoor = weather.get('is_outdoor', True)
        features.temperature = weather.get('temperature')
        features.wind_speed = weather.get('wind_speed')
        
        if not features.is_outdoor:
            features.weather_impact = 0.0
            return
        
        # Calculate weather impact
        impact = 0.0
        
        # Temperature impact (extreme cold/heat)
        temp = features.temperature
        if temp is not None:
            if temp < 32:  # Freezing
                impact += 0.02  # Slight home advantage
            elif temp > 90:  # Very hot
                impact += 0.01
        
        # Wind impact (NFL/MLB/Soccer)
        wind = features.wind_speed or 0
        if wind > 20 and sport.lower() in ['nfl', 'mlb', 'soccer']:
            impact += 0.02
        elif wind > 30:
            impact += 0.03
        
        # Precipitation (if available)
        if weather.get('precipitation', 0) > 0:
            impact += 0.02
        
        features.weather_impact = min(0.1, impact)
    
    def _apply_odds_data(self, features: MatchupFeatureVector, odds_data: Dict):
        """Apply odds data to feature vector"""
        # Implied probabilities
        home_prob = odds_data.get('home_implied_prob')
        away_prob = odds_data.get('away_implied_prob')
        
        if home_prob and away_prob:
            # Remove vig and normalize
            total = home_prob + away_prob
            if total > 0:
                features.implied_prob_home = home_prob / total
                features.implied_prob_away = away_prob / total
        
        # Spread and total lines
        features.spread_line = odds_data.get('spread')
        features.total_line = odds_data.get('total')
    
    def _calculate_data_quality(self, features: MatchupFeatureVector) -> float:
        """Calculate overall data quality score (0-100)"""
        score = 0.0
        
        # Odds data (30 points)
        if features.has_odds_data:
            score += 30
        
        # Stats data (30 points)
        if features.has_stats_data:
            score += 30
        
        # Injury data (15 points)
        if features.has_injury_data:
            score += 15
        
        # Weather data (10 points, for outdoor sports)
        if features.is_outdoor:
            if features.has_weather_data:
                score += 10
        else:
            score += 10  # Indoor, weather not needed
        
        # Recent form data (10 points)
        if features.recent_form_home != 0.5 or features.recent_form_away != 0.5:
            score += 10
        
        # H2H data (5 points)
        if features.h2h_games > 0:
            score += 5
        
        return min(100, score)
    
    def _calculate_style_matchup(self, features: MatchupFeatureVector, sport: str) -> float:
        """
        Calculate style matchup score (-1 to 1, positive favors home).
        
        Considers how team styles match up against each other.
        """
        score = 0.0
        
        # Offensive vs defensive matchups
        # Home offense vs away defense
        home_off_vs_away_def = (features.offense_rating_home - features.defense_rating_away) / 100
        # Away offense vs home defense
        away_off_vs_home_def = (features.offense_rating_away - features.defense_rating_home) / 100
        
        # Net advantage
        score += (home_off_vs_away_def - away_off_vs_home_def) * 0.3
        
        # Pace matchup (for applicable sports)
        if sport.lower() in ['nba', 'basketball_nba', 'wnba', 'basketball_wnba']:
            # High pace teams may have advantages/disadvantages based on opponent
            pace_diff = (features.pace_home - features.pace_away) / 10
            score += pace_diff * 0.1
        
        # Rest advantage
        rest_advantage = (features.rest_days_home - features.rest_days_away) * 0.01
        score += min(0.05, max(-0.05, rest_advantage))
        
        # Injury disadvantage for opponent
        injury_diff = features.injury_severity_away - features.injury_severity_home
        score += injury_diff * 0.2
        
        return max(-1.0, min(1.0, score))


# Factory function
def get_feature_pipeline(db: Optional[AsyncSession] = None) -> FeaturePipeline:
    """Get an instance of the feature pipeline"""
    return FeaturePipeline(db)

