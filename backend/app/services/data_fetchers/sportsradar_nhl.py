"""
SportsRadar NHL API Client

Fetches NHL-specific data:
- Team statistics (goals, special teams, goaltending)
- Game schedules and results
- Injury reports
- Goalie availability
"""

from typing import Dict, Optional, List
import logging
from functools import lru_cache

from app.services.data_fetchers.sportsradar_base import SportsRadarBase

logger = logging.getLogger(__name__)


class SportsRadarNHL(SportsRadarBase):
    """
    SportsRadar NHL API client.
    
    Provides NHL-specific team stats including:
    - Goals for/against
    - Power play / Penalty kill %
    - Save percentage
    - Corsi/Fenwick (if available)
    """
    
    def __init__(self):
        super().__init__(sport_code="nhl")
    
    @property
    def base_url(self) -> str:
        return "https://api.sportradar.us/nhl/trial/v7/en"
    
    # NHL team mapping: name/city -> SportsRadar team ID
    TEAM_MAP = {
        # Atlantic Division
        "bruins": "4416d559-0f24-11de-9536-ddb41ddb1138",
        "boston": "4416d559-0f24-11de-9536-ddb41ddb1138",
        "boston bruins": "4416d559-0f24-11de-9536-ddb41ddb1138",
        "sabres": "4416f332-0f24-11de-9536-ddb41ddb1138",
        "buffalo": "4416f332-0f24-11de-9536-ddb41ddb1138",
        "buffalo sabres": "4416f332-0f24-11de-9536-ddb41ddb1138",
        "red wings": "4416091c-0f24-11de-9536-ddb41ddb1138",
        "detroit": "4416091c-0f24-11de-9536-ddb41ddb1138",
        "detroit red wings": "4416091c-0f24-11de-9536-ddb41ddb1138",
        "panthers": "4415b0a7-0f24-11de-9536-ddb41ddb1138",
        "florida": "4415b0a7-0f24-11de-9536-ddb41ddb1138",
        "florida panthers": "4415b0a7-0f24-11de-9536-ddb41ddb1138",
        "canadiens": "4415b7a6-0f24-11de-9536-ddb41ddb1138",
        "habs": "4415b7a6-0f24-11de-9536-ddb41ddb1138",
        "montreal": "4415b7a6-0f24-11de-9536-ddb41ddb1138",
        "montreal canadiens": "4415b7a6-0f24-11de-9536-ddb41ddb1138",
        "senators": "4416272b-0f24-11de-9536-ddb41ddb1138",
        "ottawa": "4416272b-0f24-11de-9536-ddb41ddb1138",
        "ottawa senators": "4416272b-0f24-11de-9536-ddb41ddb1138",
        "lightning": "4416bb16-0f24-11de-9536-ddb41ddb1138",
        "tampa bay": "4416bb16-0f24-11de-9536-ddb41ddb1138",
        "tampa bay lightning": "4416bb16-0f24-11de-9536-ddb41ddb1138",
        "maple leafs": "4415b5a0-0f24-11de-9536-ddb41ddb1138",
        "leafs": "4415b5a0-0f24-11de-9536-ddb41ddb1138",
        "toronto": "4415b5a0-0f24-11de-9536-ddb41ddb1138",
        "toronto maple leafs": "4415b5a0-0f24-11de-9536-ddb41ddb1138",
        
        # Metropolitan Division
        "hurricanes": "44154b9f-0f24-11de-9536-ddb41ddb1138",
        "canes": "44154b9f-0f24-11de-9536-ddb41ddb1138",
        "carolina": "44154b9f-0f24-11de-9536-ddb41ddb1138",
        "carolina hurricanes": "44154b9f-0f24-11de-9536-ddb41ddb1138",
        "blue jackets": "4415b0a0-0f24-11de-9536-ddb41ddb1138",
        "jackets": "4415b0a0-0f24-11de-9536-ddb41ddb1138",
        "columbus": "4415b0a0-0f24-11de-9536-ddb41ddb1138",
        "columbus blue jackets": "4415b0a0-0f24-11de-9536-ddb41ddb1138",
        "devils": "44150c28-0f24-11de-9536-ddb41ddb1138",
        "new jersey": "44150c28-0f24-11de-9536-ddb41ddb1138",
        "new jersey devils": "44150c28-0f24-11de-9536-ddb41ddb1138",
        "islanders": "4416c12c-0f24-11de-9536-ddb41ddb1138",
        "isles": "4416c12c-0f24-11de-9536-ddb41ddb1138",
        "new york islanders": "4416c12c-0f24-11de-9536-ddb41ddb1138",
        "rangers": "4415c231-0f24-11de-9536-ddb41ddb1138",
        "new york rangers": "4415c231-0f24-11de-9536-ddb41ddb1138",
        "flyers": "441660ea-0f24-11de-9536-ddb41ddb1138",
        "philadelphia": "441660ea-0f24-11de-9536-ddb41ddb1138",
        "philadelphia flyers": "441660ea-0f24-11de-9536-ddb41ddb1138",
        "penguins": "4416577a-0f24-11de-9536-ddb41ddb1138",
        "pens": "4416577a-0f24-11de-9536-ddb41ddb1138",
        "pittsburgh": "4416577a-0f24-11de-9536-ddb41ddb1138",
        "pittsburgh penguins": "4416577a-0f24-11de-9536-ddb41ddb1138",
        "capitals": "4416eabd-0f24-11de-9536-ddb41ddb1138",
        "caps": "4416eabd-0f24-11de-9536-ddb41ddb1138",
        "washington": "4416eabd-0f24-11de-9536-ddb41ddb1138",
        "washington capitals": "4416eabd-0f24-11de-9536-ddb41ddb1138",
        
        # Central Division
        "coyotes": "44154cf7-0f24-11de-9536-ddb41ddb1138",
        "arizona": "44154cf7-0f24-11de-9536-ddb41ddb1138",
        "arizona coyotes": "44154cf7-0f24-11de-9536-ddb41ddb1138",
        "blackhawks": "44159241-0f24-11de-9536-ddb41ddb1138",
        "hawks": "44159241-0f24-11de-9536-ddb41ddb1138",
        "chicago": "44159241-0f24-11de-9536-ddb41ddb1138",
        "chicago blackhawks": "44159241-0f24-11de-9536-ddb41ddb1138",
        "avalanche": "4415ce41-0f24-11de-9536-ddb41ddb1138",
        "avs": "4415ce41-0f24-11de-9536-ddb41ddb1138",
        "colorado": "4415ce41-0f24-11de-9536-ddb41ddb1138",
        "colorado avalanche": "4415ce41-0f24-11de-9536-ddb41ddb1138",
        "stars": "441615e8-0f24-11de-9536-ddb41ddb1138",
        "dallas": "441615e8-0f24-11de-9536-ddb41ddb1138",
        "dallas stars": "441615e8-0f24-11de-9536-ddb41ddb1138",
        "wild": "44157ba8-0f24-11de-9536-ddb41ddb1138",
        "minnesota": "44157ba8-0f24-11de-9536-ddb41ddb1138",
        "minnesota wild": "44157ba8-0f24-11de-9536-ddb41ddb1138",
        "predators": "4415cd5f-0f24-11de-9536-ddb41ddb1138",
        "preds": "4415cd5f-0f24-11de-9536-ddb41ddb1138",
        "nashville": "4415cd5f-0f24-11de-9536-ddb41ddb1138",
        "nashville predators": "4415cd5f-0f24-11de-9536-ddb41ddb1138",
        "blues": "441689b9-0f24-11de-9536-ddb41ddb1138",
        "st louis": "441689b9-0f24-11de-9536-ddb41ddb1138",
        "st. louis": "441689b9-0f24-11de-9536-ddb41ddb1138",
        "st. louis blues": "441689b9-0f24-11de-9536-ddb41ddb1138",
        "jets": "44163d20-0f24-11de-9536-ddb41ddb1138",
        "winnipeg": "44163d20-0f24-11de-9536-ddb41ddb1138",
        "winnipeg jets": "44163d20-0f24-11de-9536-ddb41ddb1138",
        
        # Pacific Division
        "ducks": "44152321-0f24-11de-9536-ddb41ddb1138",
        "anaheim": "44152321-0f24-11de-9536-ddb41ddb1138",
        "anaheim ducks": "44152321-0f24-11de-9536-ddb41ddb1138",
        "flames": "441641a1-0f24-11de-9536-ddb41ddb1138",
        "calgary": "441641a1-0f24-11de-9536-ddb41ddb1138",
        "calgary flames": "441641a1-0f24-11de-9536-ddb41ddb1138",
        "oilers": "4415c5b0-0f24-11de-9536-ddb41ddb1138",
        "edmonton": "4415c5b0-0f24-11de-9536-ddb41ddb1138",
        "edmonton oilers": "4415c5b0-0f24-11de-9536-ddb41ddb1138",
        "kings": "44166e5f-0f24-11de-9536-ddb41ddb1138",
        "la kings": "44166e5f-0f24-11de-9536-ddb41ddb1138",
        "los angeles": "44166e5f-0f24-11de-9536-ddb41ddb1138",
        "los angeles kings": "44166e5f-0f24-11de-9536-ddb41ddb1138",
        "sharks": "44153428-0f24-11de-9536-ddb41ddb1138",
        "san jose": "44153428-0f24-11de-9536-ddb41ddb1138",
        "san jose sharks": "44153428-0f24-11de-9536-ddb41ddb1138",
        "kraken": "44155906-0f24-11de-9536-ddb41ddb1138",
        "seattle": "44155906-0f24-11de-9536-ddb41ddb1138",
        "seattle kraken": "44155906-0f24-11de-9536-ddb41ddb1138",
        "canucks": "44157bb5-0f24-11de-9536-ddb41ddb1138",
        "vancouver": "44157bb5-0f24-11de-9536-ddb41ddb1138",
        "vancouver canucks": "44157bb5-0f24-11de-9536-ddb41ddb1138",
        "golden knights": "44153296-0f24-11de-9536-ddb41ddb1138",
        "knights": "44153296-0f24-11de-9536-ddb41ddb1138",
        "vegas": "44153296-0f24-11de-9536-ddb41ddb1138",
        "vegas golden knights": "44153296-0f24-11de-9536-ddb41ddb1138",
    }
    
    # NHL position importance weights (goalie is critical)
    POSITION_WEIGHTS = {
        "G": 0.5,     # Goalie is most important
        "D": 0.25,    # Defensemen
        "C": 0.3,     # Center (face-offs, two-way play)
        "LW": 0.2,    # Left wing
        "RW": 0.2,    # Right wing
        "F": 0.2,     # Generic forward
    }
    
    def _normalize_team_name(self, team_name: str) -> Optional[str]:
        """Convert team name to SportsRadar team ID"""
        normalized = team_name.lower().strip()
        return self.TEAM_MAP.get(normalized)
    
    def _get_position_importance(self, position: str) -> float:
        """Get importance weight for NHL position"""
        return self.POSITION_WEIGHTS.get(position.upper(), 0.15)
    
    def _parse_team_stats(self, data: Dict) -> Dict:
        """Parse NHL team statistics from SportsRadar response"""
        team = data.get('team', data)
        stats = data.get('statistics', data.get('own_record', {}))
        
        # Parse record
        record = stats.get('record', {})
        wins = record.get('wins', 0)
        losses = record.get('losses', 0)
        ot_losses = record.get('overtime', record.get('ot_losses', 0))
        games_played = wins + losses + ot_losses
        
        # Parse offensive stats
        offense = self._parse_offense_stats(stats)
        
        # Parse defensive stats
        defense = self._parse_defense_stats(stats)
        
        # Parse special teams
        special_teams = self._parse_special_teams(stats)
        
        return {
            'name': team.get('name', team.get('market', '')),
            'abbreviation': team.get('alias', ''),
            'record': {
                'wins': wins,
                'losses': losses,
                'ot_losses': ot_losses,
                'points': wins * 2 + ot_losses,
                'win_percentage': wins / games_played if games_played > 0 else 0,
            },
            'offense': offense,
            'defense': defense,
            'special_teams': special_teams,
            'efficiency': {
                'goal_differential': offense.get('goals_per_game', 0) - defense.get('goals_allowed_per_game', 0),
                'offensive_efficiency': self._calculate_offensive_efficiency(offense, special_teams),
                'defensive_efficiency': self._calculate_defensive_efficiency(defense, special_teams),
            },
            'situational': {
                'home_record': self._parse_split_record(stats.get('home', {})),
                'away_record': self._parse_split_record(stats.get('road', {})),
            }
        }
    
    def _parse_offense_stats(self, stats: Dict) -> Dict:
        """Parse NHL offensive statistics"""
        games = max(1, stats.get('games_played', 1))
        scoring = stats.get('scoring', stats)
        
        return {
            'goals_per_game': scoring.get('goals', 0) / games,
            'shots_per_game': scoring.get('shots', 0) / games,
            'shooting_pct': scoring.get('shooting_pct', 0),
            'assists_per_game': scoring.get('assists', 0) / games,
            'first_goals': scoring.get('first_goals', 0),
            'power_play_goals': stats.get('power_play', {}).get('goals', 0),
        }
    
    def _parse_defense_stats(self, stats: Dict) -> Dict:
        """Parse NHL defensive statistics"""
        games = max(1, stats.get('games_played', 1))
        goaltending = stats.get('goaltending', {})
        
        return {
            'goals_allowed_per_game': goaltending.get('goals_against', 0) / games,
            'shots_against_per_game': goaltending.get('shots_against', 0) / games,
            'save_pct': goaltending.get('saves_pct', goaltending.get('save_pct', 0)),
            'shutouts': goaltending.get('shutouts', 0),
            'hits_per_game': stats.get('hits', 0) / games,
            'blocked_shots_per_game': stats.get('blocked_shots', 0) / games,
        }
    
    def _parse_special_teams(self, stats: Dict) -> Dict:
        """Parse NHL special teams statistics"""
        pp = stats.get('power_play', {})
        pk = stats.get('penalty_kill', stats.get('shorthanded', {}))
        
        return {
            'power_play_pct': pp.get('pct', pp.get('percentage', 0)),
            'power_play_goals': pp.get('goals', 0),
            'power_play_opportunities': pp.get('opportunities', pp.get('count', 0)),
            'penalty_kill_pct': pk.get('pct', pk.get('percentage', 0)),
            'shorthanded_goals': pk.get('goals', 0),
            'penalties_per_game': stats.get('penalties', 0) / max(1, stats.get('games_played', 1)),
        }
    
    def _parse_split_record(self, split: Dict) -> Dict:
        """Parse a record split (home/away)"""
        return {
            'wins': split.get('wins', 0),
            'losses': split.get('losses', 0),
            'ot_losses': split.get('overtime', split.get('ot_losses', 0)),
        }
    
    def _calculate_offensive_efficiency(self, offense: Dict, special_teams: Dict) -> float:
        """
        Calculate offensive efficiency score (0-100).
        NHL-specific: goals, shots, power play.
        """
        # Goals per game (league avg ~3.0)
        gpg = offense.get('goals_per_game', 3.0)
        gpg_score = min(100, (gpg / 4.0) * 100)
        
        # Shooting percentage (league avg ~10%)
        shooting = offense.get('shooting_pct', 10)
        shooting_score = min(100, shooting * 8)
        
        # Power play (league avg ~20%)
        pp_pct = special_teams.get('power_play_pct', 20)
        pp_score = min(100, pp_pct * 4)
        
        efficiency = (gpg_score * 0.4 + shooting_score * 0.3 + pp_score * 0.3)
        return round(max(0, min(100, efficiency)), 1)
    
    def _calculate_defensive_efficiency(self, defense: Dict, special_teams: Dict) -> float:
        """
        Calculate defensive efficiency score (0-100).
        NHL-specific: goals against, save %, penalty kill.
        """
        # Goals against per game (lower is better, league avg ~3.0)
        gapg = defense.get('goals_allowed_per_game', 3.0)
        gapg_score = min(100, max(0, (4.0 - gapg) / 2.0 * 100))
        
        # Save percentage (league avg ~.905)
        save_pct = defense.get('save_pct', 0.905)
        save_score = min(100, max(0, (save_pct - 0.88) / 0.04 * 100))
        
        # Penalty kill (league avg ~80%)
        pk_pct = special_teams.get('penalty_kill_pct', 80)
        pk_score = min(100, (pk_pct - 70) * 3)
        
        efficiency = (gapg_score * 0.35 + save_score * 0.4 + pk_score * 0.25)
        return round(max(0, min(100, efficiency)), 1)


# Factory function for easy import
@lru_cache(maxsize=1)
def get_nhl_fetcher() -> SportsRadarNHL:
    """Get an instance of the NHL SportsRadar fetcher"""
    return SportsRadarNHL()

