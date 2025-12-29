"""
SportsRadar NBA API Client

Fetches NBA-specific data:
- Team statistics (offensive/defensive rating, pace)
- Game schedules and results
- Injury reports
- Player availability
"""

from typing import Dict, Optional, List
import logging
from functools import lru_cache

from app.services.data_fetchers.sportsradar_base import SportsRadarBase

logger = logging.getLogger(__name__)


class SportsRadarNBA(SportsRadarBase):
    """
    SportsRadar NBA API client.
    
    Provides NBA-specific team stats including advanced metrics like:
    - Offensive/Defensive Rating
    - Pace (possessions per game)
    - True Shooting %
    - Rebound rate
    """
    
    def __init__(self):
        super().__init__(sport_code="nba")
    
    @property
    def base_url(self) -> str:
        return "https://api.sportradar.us/nba/trial/v8/en"
    
    # NBA team mapping: name/city -> SportsRadar team ID
    TEAM_MAP = {
        # Atlantic Division
        "celtics": "583eccfa-fb46-11e1-82cb-f4ce4684ea4c",
        "boston": "583eccfa-fb46-11e1-82cb-f4ce4684ea4c",
        "boston celtics": "583eccfa-fb46-11e1-82cb-f4ce4684ea4c",
        "nets": "583ec9a8-fb46-11e1-82cb-f4ce4684ea4c",
        "brooklyn": "583ec9a8-fb46-11e1-82cb-f4ce4684ea4c",
        "brooklyn nets": "583ec9a8-fb46-11e1-82cb-f4ce4684ea4c",
        "knicks": "583ec70e-fb46-11e1-82cb-f4ce4684ea4c",
        "new york": "583ec70e-fb46-11e1-82cb-f4ce4684ea4c",
        "new york knicks": "583ec70e-fb46-11e1-82cb-f4ce4684ea4c",
        "76ers": "583ec87d-fb46-11e1-82cb-f4ce4684ea4c",
        "sixers": "583ec87d-fb46-11e1-82cb-f4ce4684ea4c",
        "philadelphia": "583ec87d-fb46-11e1-82cb-f4ce4684ea4c",
        "philadelphia 76ers": "583ec87d-fb46-11e1-82cb-f4ce4684ea4c",
        "raptors": "583ecda6-fb46-11e1-82cb-f4ce4684ea4c",
        "toronto": "583ecda6-fb46-11e1-82cb-f4ce4684ea4c",
        "toronto raptors": "583ecda6-fb46-11e1-82cb-f4ce4684ea4c",
        
        # Central Division
        "bulls": "583ec5fd-fb46-11e1-82cb-f4ce4684ea4c",
        "chicago": "583ec5fd-fb46-11e1-82cb-f4ce4684ea4c",
        "chicago bulls": "583ec5fd-fb46-11e1-82cb-f4ce4684ea4c",
        "cavaliers": "583ec773-fb46-11e1-82cb-f4ce4684ea4c",
        "cavs": "583ec773-fb46-11e1-82cb-f4ce4684ea4c",
        "cleveland": "583ec773-fb46-11e1-82cb-f4ce4684ea4c",
        "cleveland cavaliers": "583ec773-fb46-11e1-82cb-f4ce4684ea4c",
        "pistons": "583ec928-fb46-11e1-82cb-f4ce4684ea4c",
        "detroit": "583ec928-fb46-11e1-82cb-f4ce4684ea4c",
        "detroit pistons": "583ec928-fb46-11e1-82cb-f4ce4684ea4c",
        "pacers": "583ec7cd-fb46-11e1-82cb-f4ce4684ea4c",
        "indiana": "583ec7cd-fb46-11e1-82cb-f4ce4684ea4c",
        "indiana pacers": "583ec7cd-fb46-11e1-82cb-f4ce4684ea4c",
        "bucks": "583ecefd-fb46-11e1-82cb-f4ce4684ea4c",
        "milwaukee": "583ecefd-fb46-11e1-82cb-f4ce4684ea4c",
        "milwaukee bucks": "583ecefd-fb46-11e1-82cb-f4ce4684ea4c",
        
        # Southeast Division
        "hawks": "583ecb8f-fb46-11e1-82cb-f4ce4684ea4c",
        "atlanta": "583ecb8f-fb46-11e1-82cb-f4ce4684ea4c",
        "atlanta hawks": "583ecb8f-fb46-11e1-82cb-f4ce4684ea4c",
        "hornets": "583ec97e-fb46-11e1-82cb-f4ce4684ea4c",
        "charlotte": "583ec97e-fb46-11e1-82cb-f4ce4684ea4c",
        "charlotte hornets": "583ec97e-fb46-11e1-82cb-f4ce4684ea4c",
        "heat": "583ecea6-fb46-11e1-82cb-f4ce4684ea4c",
        "miami": "583ecea6-fb46-11e1-82cb-f4ce4684ea4c",
        "miami heat": "583ecea6-fb46-11e1-82cb-f4ce4684ea4c",
        "magic": "583ed157-fb46-11e1-82cb-f4ce4684ea4c",
        "orlando": "583ed157-fb46-11e1-82cb-f4ce4684ea4c",
        "orlando magic": "583ed157-fb46-11e1-82cb-f4ce4684ea4c",
        "wizards": "583ec8d4-fb46-11e1-82cb-f4ce4684ea4c",
        "washington": "583ec8d4-fb46-11e1-82cb-f4ce4684ea4c",
        "washington wizards": "583ec8d4-fb46-11e1-82cb-f4ce4684ea4c",
        
        # Northwest Division
        "nuggets": "583ed102-fb46-11e1-82cb-f4ce4684ea4c",
        "denver": "583ed102-fb46-11e1-82cb-f4ce4684ea4c",
        "denver nuggets": "583ed102-fb46-11e1-82cb-f4ce4684ea4c",
        "timberwolves": "583eca2f-fb46-11e1-82cb-f4ce4684ea4c",
        "wolves": "583eca2f-fb46-11e1-82cb-f4ce4684ea4c",
        "minnesota": "583eca2f-fb46-11e1-82cb-f4ce4684ea4c",
        "minnesota timberwolves": "583eca2f-fb46-11e1-82cb-f4ce4684ea4c",
        "thunder": "583ecfff-fb46-11e1-82cb-f4ce4684ea4c",
        "okc": "583ecfff-fb46-11e1-82cb-f4ce4684ea4c",
        "oklahoma city": "583ecfff-fb46-11e1-82cb-f4ce4684ea4c",
        "oklahoma city thunder": "583ecfff-fb46-11e1-82cb-f4ce4684ea4c",
        "trail blazers": "583ed056-fb46-11e1-82cb-f4ce4684ea4c",
        "blazers": "583ed056-fb46-11e1-82cb-f4ce4684ea4c",
        "portland": "583ed056-fb46-11e1-82cb-f4ce4684ea4c",
        "portland trail blazers": "583ed056-fb46-11e1-82cb-f4ce4684ea4c",
        "jazz": "583ece50-fb46-11e1-82cb-f4ce4684ea4c",
        "utah": "583ece50-fb46-11e1-82cb-f4ce4684ea4c",
        "utah jazz": "583ece50-fb46-11e1-82cb-f4ce4684ea4c",
        
        # Pacific Division
        "warriors": "583ec825-fb46-11e1-82cb-f4ce4684ea4c",
        "golden state": "583ec825-fb46-11e1-82cb-f4ce4684ea4c",
        "golden state warriors": "583ec825-fb46-11e1-82cb-f4ce4684ea4c",
        "clippers": "583ecdfb-fb46-11e1-82cb-f4ce4684ea4c",
        "la clippers": "583ecdfb-fb46-11e1-82cb-f4ce4684ea4c",
        "los angeles clippers": "583ecdfb-fb46-11e1-82cb-f4ce4684ea4c",
        "lakers": "583ecae2-fb46-11e1-82cb-f4ce4684ea4c",
        "la lakers": "583ecae2-fb46-11e1-82cb-f4ce4684ea4c",
        "los angeles lakers": "583ecae2-fb46-11e1-82cb-f4ce4684ea4c",
        "suns": "583ecfa8-fb46-11e1-82cb-f4ce4684ea4c",
        "phoenix": "583ecfa8-fb46-11e1-82cb-f4ce4684ea4c",
        "phoenix suns": "583ecfa8-fb46-11e1-82cb-f4ce4684ea4c",
        "kings": "583ed0ac-fb46-11e1-82cb-f4ce4684ea4c",
        "sacramento": "583ed0ac-fb46-11e1-82cb-f4ce4684ea4c",
        "sacramento kings": "583ed0ac-fb46-11e1-82cb-f4ce4684ea4c",
        
        # Southwest Division
        "mavericks": "583ecf50-fb46-11e1-82cb-f4ce4684ea4c",
        "mavs": "583ecf50-fb46-11e1-82cb-f4ce4684ea4c",
        "dallas": "583ecf50-fb46-11e1-82cb-f4ce4684ea4c",
        "dallas mavericks": "583ecf50-fb46-11e1-82cb-f4ce4684ea4c",
        "rockets": "583ecb3a-fb46-11e1-82cb-f4ce4684ea4c",
        "houston": "583ecb3a-fb46-11e1-82cb-f4ce4684ea4c",
        "houston rockets": "583ecb3a-fb46-11e1-82cb-f4ce4684ea4c",
        "grizzlies": "583eca88-fb46-11e1-82cb-f4ce4684ea4c",
        "memphis": "583eca88-fb46-11e1-82cb-f4ce4684ea4c",
        "memphis grizzlies": "583eca88-fb46-11e1-82cb-f4ce4684ea4c",
        "pelicans": "583ecc9a-fb46-11e1-82cb-f4ce4684ea4c",
        "new orleans": "583ecc9a-fb46-11e1-82cb-f4ce4684ea4c",
        "new orleans pelicans": "583ecc9a-fb46-11e1-82cb-f4ce4684ea4c",
        "spurs": "583ecd4f-fb46-11e1-82cb-f4ce4684ea4c",
        "san antonio": "583ecd4f-fb46-11e1-82cb-f4ce4684ea4c",
        "san antonio spurs": "583ecd4f-fb46-11e1-82cb-f4ce4684ea4c",
    }
    
    # NBA position importance weights
    POSITION_WEIGHTS = {
        "PG": 0.35,   # Point guard - floor general
        "SG": 0.25,   # Shooting guard
        "SF": 0.25,   # Small forward
        "PF": 0.2,    # Power forward
        "C": 0.25,    # Center
        "G": 0.3,     # Generic guard
        "F": 0.2,     # Generic forward
    }
    
    def _normalize_team_name(self, team_name: str) -> Optional[str]:
        """Convert team name to SportsRadar team ID"""
        normalized = team_name.lower().strip()
        return self.TEAM_MAP.get(normalized)
    
    def _get_position_importance(self, position: str) -> float:
        """Get importance weight for NBA position"""
        return self.POSITION_WEIGHTS.get(position.upper(), 0.2)
    
    def _parse_team_stats(self, data: Dict) -> Dict:
        """Parse NBA team statistics from SportsRadar response"""
        team = data.get('team', data)
        stats = data.get('own_record', data.get('statistics', {}))
        
        # Parse record
        wins = stats.get('wins', 0)
        losses = stats.get('losses', 0)
        games_played = wins + losses
        
        # Parse offensive stats
        offense = self._parse_offense_stats(stats)
        
        # Parse defensive stats
        defense = self._parse_defense_stats(data.get('opponents', {}))
        
        # Advanced stats
        pace = stats.get('pace', 100)
        off_rating = stats.get('offensive_rating', stats.get('efficiency', 110))
        def_rating = data.get('opponents', {}).get('offensive_rating', 110)
        
        return {
            'name': team.get('name', team.get('market', '')),
            'abbreviation': team.get('alias', ''),
            'record': {
                'wins': wins,
                'losses': losses,
                'win_percentage': wins / games_played if games_played > 0 else 0,
            },
            'offense': offense,
            'defense': defense,
            'advanced': {
                'pace': pace,
                'offensive_rating': off_rating,
                'defensive_rating': def_rating,
                'net_rating': off_rating - def_rating,
                'true_shooting_pct': stats.get('true_shooting_pct', 0),
                'effective_fg_pct': stats.get('effective_fg_pct', 0),
            },
            'efficiency': {
                'offensive_efficiency': self._calculate_offensive_efficiency(offense, off_rating),
                'defensive_efficiency': self._calculate_defensive_efficiency(defense, def_rating),
            },
            'situational': {
                'home_record': self._parse_split_record(stats.get('home', {})),
                'away_record': self._parse_split_record(stats.get('road', {})),
            }
        }
    
    def _parse_offense_stats(self, stats: Dict) -> Dict:
        """Parse NBA offensive statistics"""
        return {
            'points_per_game': stats.get('points', 0) / max(1, stats.get('games_played', 1)),
            'field_goal_pct': stats.get('field_goal_pct', 0),
            'three_point_pct': stats.get('three_point_pct', 0),
            'free_throw_pct': stats.get('free_throw_pct', 0),
            'assists_per_game': stats.get('assists', 0) / max(1, stats.get('games_played', 1)),
            'turnovers_per_game': stats.get('turnovers', 0) / max(1, stats.get('games_played', 1)),
            'rebounds_per_game': stats.get('rebounds', 0) / max(1, stats.get('games_played', 1)),
            'offensive_rebounds': stats.get('off_rebounds', 0) / max(1, stats.get('games_played', 1)),
        }
    
    def _parse_defense_stats(self, opponents: Dict) -> Dict:
        """Parse NBA defensive statistics (opponent stats)"""
        games = max(1, opponents.get('games_played', 1))
        return {
            'points_allowed_per_game': opponents.get('points', 0) / games,
            'opponent_fg_pct': opponents.get('field_goal_pct', 0),
            'opponent_3pt_pct': opponents.get('three_point_pct', 0),
            'steals_per_game': opponents.get('steals', 0) / games,
            'blocks_per_game': opponents.get('blocks', 0) / games,
            'defensive_rebounds': opponents.get('def_rebounds', 0) / games,
        }
    
    def _parse_split_record(self, split: Dict) -> Dict:
        """Parse a record split (home/away)"""
        return {
            'wins': split.get('wins', 0),
            'losses': split.get('losses', 0),
        }
    
    def _calculate_offensive_efficiency(self, offense: Dict, off_rating: float) -> float:
        """
        Calculate offensive efficiency score (0-100).
        NBA-specific: emphasizes pace, 3PT%, and assist rate.
        """
        # Offensive rating is on ~100-120 scale typically
        rating_score = min(100, max(0, (off_rating - 100) * 5))
        
        # Three point shooting (league avg ~36%)
        three_pt_score = min(100, offense.get('three_point_pct', 36) / 45 * 100)
        
        # Assist to turnover
        ast = offense.get('assists_per_game', 20)
        to = max(1, offense.get('turnovers_per_game', 15))
        ast_to_score = min(100, (ast / to) * 30)
        
        efficiency = (rating_score * 0.5 + three_pt_score * 0.25 + ast_to_score * 0.25)
        return round(max(0, min(100, efficiency)), 1)
    
    def _calculate_defensive_efficiency(self, defense: Dict, def_rating: float) -> float:
        """
        Calculate defensive efficiency score (0-100).
        Lower defensive rating = better defense.
        """
        # Defensive rating is on ~100-120 scale (lower is better)
        rating_score = min(100, max(0, (120 - def_rating) * 5))
        
        # Opponent FG% (lower is better)
        opp_fg = defense.get('opponent_fg_pct', 46)
        fg_score = min(100, max(0, (50 - opp_fg) * 10 + 50))
        
        # Steals + blocks
        steals = defense.get('steals_per_game', 7)
        blocks = defense.get('blocks_per_game', 5)
        active_d_score = min(100, (steals + blocks) * 5)
        
        efficiency = (rating_score * 0.5 + fg_score * 0.3 + active_d_score * 0.2)
        return round(max(0, min(100, efficiency)), 1)


# Factory function for easy import
@lru_cache(maxsize=1)
def get_nba_fetcher() -> SportsRadarNBA:
    """Get an instance of the NBA SportsRadar fetcher"""
    return SportsRadarNBA()

