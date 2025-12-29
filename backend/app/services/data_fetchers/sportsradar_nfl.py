"""
SportsRadar NFL API Client

Fetches NFL-specific data:
- Team statistics (offense, defense, special teams)
- Game schedules and results
- Injury reports
- Player data
"""

from typing import Dict, Optional, List
import logging
from functools import lru_cache

from app.services.data_fetchers.sportsradar_base import SportsRadarBase

logger = logging.getLogger(__name__)


class SportsRadarNFL(SportsRadarBase):
    """
    SportsRadar NFL API client.
    
    Provides NFL-specific team stats, schedules, and injury data.
    Falls back to ESPN data when SportsRadar is unavailable.
    """
    
    def __init__(self):
        super().__init__(sport_code="nfl")
    
    @property
    def base_url(self) -> str:
        return "https://api.sportradar.us/nfl/official/trial/v7/en"
    
    # NFL team mapping: name/city -> SportsRadar team ID
    TEAM_MAP = {
        # AFC East
        "ravens": "ebd87119-b331-4469-9ea6-d51fe3ce2f1c",
        "baltimore": "ebd87119-b331-4469-9ea6-d51fe3ce2f1c",
        "baltimore ravens": "ebd87119-b331-4469-9ea6-d51fe3ce2f1c",
        "bills": "768c92aa-75ff-4a43-bcc0-f2798c2e1724",
        "buffalo": "768c92aa-75ff-4a43-bcc0-f2798c2e1724",
        "buffalo bills": "768c92aa-75ff-4a43-bcc0-f2798c2e1724",
        "dolphins": "4809ecb0-abd3-451d-9c4a-92a90b83ca06",
        "miami": "4809ecb0-abd3-451d-9c4a-92a90b83ca06",
        "miami dolphins": "4809ecb0-abd3-451d-9c4a-92a90b83ca06",
        "patriots": "e6aa13a4-0055-48a9-bc41-be28dc106929",
        "new england": "e6aa13a4-0055-48a9-bc41-be28dc106929",
        "new england patriots": "e6aa13a4-0055-48a9-bc41-be28dc106929",
        "jets": "5fee86ae-74ab-4f0d-9c78-bf62d21d5d52",
        "new york jets": "5fee86ae-74ab-4f0d-9c78-bf62d21d5d52",
        
        # AFC North
        "bengals": "ad4ae08f-d808-42d5-a1e6-e9bc4e34d123",
        "cincinnati": "ad4ae08f-d808-42d5-a1e6-e9bc4e34d123",
        "cincinnati bengals": "ad4ae08f-d808-42d5-a1e6-e9bc4e34d123",
        "browns": "d5a2eb42-8065-4174-ab79-0a6fa820e35e",
        "cleveland": "d5a2eb42-8065-4174-ab79-0a6fa820e35e",
        "cleveland browns": "d5a2eb42-8065-4174-ab79-0a6fa820e35e",
        "steelers": "cb2f9f1f-ac67-424e-9e72-1475cb0ed398",
        "pittsburgh": "cb2f9f1f-ac67-424e-9e72-1475cb0ed398",
        "pittsburgh steelers": "cb2f9f1f-ac67-424e-9e72-1475cb0ed398",
        
        # AFC South
        "texans": "82d2d380-3834-4938-835f-aec541e5edd7",
        "houston": "82d2d380-3834-4938-835f-aec541e5edd7",
        "houston texans": "82d2d380-3834-4938-835f-aec541e5edd7",
        "colts": "82cf9565-6eb9-4f01-bdbd-5aa0d472fcd9",
        "indianapolis": "82cf9565-6eb9-4f01-bdbd-5aa0d472fcd9",
        "indianapolis colts": "82cf9565-6eb9-4f01-bdbd-5aa0d472fcd9",
        "jaguars": "f7ddd7fa-0571-43cf-9c03-eb12f7034fcb",
        "jacksonville": "f7ddd7fa-0571-43cf-9c03-eb12f7034fcb",
        "jacksonville jaguars": "f7ddd7fa-0571-43cf-9c03-eb12f7034fcb",
        "titans": "d26a1ca5-722d-4274-8f97-c92e49c96f04",
        "tennessee": "d26a1ca5-722d-4274-8f97-c92e49c96f04",
        "tennessee titans": "d26a1ca5-722d-4274-8f97-c92e49c96f04",
        
        # AFC West
        "broncos": "ce92bd47-93d5-4fe9-ada4-0fc681e6caa0",
        "denver": "ce92bd47-93d5-4fe9-ada4-0fc681e6caa0",
        "denver broncos": "ce92bd47-93d5-4fe9-ada4-0fc681e6caa0",
        "chiefs": "6680d28d-d4d2-49f6-aace-5292d3ec02c2",
        "kansas city": "6680d28d-d4d2-49f6-aace-5292d3ec02c2",
        "kansas city chiefs": "6680d28d-d4d2-49f6-aace-5292d3ec02c2",
        "raiders": "7d4fcc64-9cb5-4d1b-8e75-8a906d1e1576",
        "las vegas": "7d4fcc64-9cb5-4d1b-8e75-8a906d1e1576",
        "las vegas raiders": "7d4fcc64-9cb5-4d1b-8e75-8a906d1e1576",
        "chargers": "1f6dcffb-9823-43cd-9ff4-e7a8466749b5",
        "los angeles chargers": "1f6dcffb-9823-43cd-9ff4-e7a8466749b5",
        
        # NFC East
        "cowboys": "e627eec7-bbae-4f54-8883-fc084e5e2fc1",
        "dallas": "e627eec7-bbae-4f54-8883-fc084e5e2fc1",
        "dallas cowboys": "e627eec7-bbae-4f54-8883-fc084e5e2fc1",
        "giants": "04aa1c9d-66da-489d-b16a-1dee3f2eec4d",
        "new york giants": "04aa1c9d-66da-489d-b16a-1dee3f2eec4d",
        "eagles": "386bdbf9-9eea-4869-bb9a-274b0bc66e80",
        "philadelphia": "386bdbf9-9eea-4869-bb9a-274b0bc66e80",
        "philadelphia eagles": "386bdbf9-9eea-4869-bb9a-274b0bc66e80",
        "commanders": "22052ff7-c065-42ee-bc8f-c4691c50e624",
        "washington": "22052ff7-c065-42ee-bc8f-c4691c50e624",
        "washington commanders": "22052ff7-c065-42ee-bc8f-c4691c50e624",
        
        # NFC North
        "bears": "7b077e6f-3686-43a2-ac4a-3a0ff95e42c9",
        "chicago": "7b077e6f-3686-43a2-ac4a-3a0ff95e42c9",
        "chicago bears": "7b077e6f-3686-43a2-ac4a-3a0ff95e42c9",
        "lions": "c5a59daa-53a7-4de0-851f-fb12be893e9e",
        "detroit": "c5a59daa-53a7-4de0-851f-fb12be893e9e",
        "detroit lions": "c5a59daa-53a7-4de0-851f-fb12be893e9e",
        "packers": "a20c96bb-2213-4e9d-8e07-ae9c4e6f9d50",
        "green bay": "a20c96bb-2213-4e9d-8e07-ae9c4e6f9d50",
        "green bay packers": "a20c96bb-2213-4e9d-8e07-ae9c4e6f9d50",
        "vikings": "33405046-04ee-4058-a950-d606f8c30852",
        "minnesota": "33405046-04ee-4058-a950-d606f8c30852",
        "minnesota vikings": "33405046-04ee-4058-a950-d606f8c30852",
        
        # NFC South
        "falcons": "e6aa13a4-0055-48a9-bc41-be28dc106929",
        "atlanta": "e6aa13a4-0055-48a9-bc41-be28dc106929",
        "atlanta falcons": "e6aa13a4-0055-48a9-bc41-be28dc106929",
        "panthers": "f14bf5cc-9a82-4a38-bc15-d39f75ed5314",
        "carolina": "f14bf5cc-9a82-4a38-bc15-d39f75ed5314",
        "carolina panthers": "f14bf5cc-9a82-4a38-bc15-d39f75ed5314",
        "saints": "0d855753-ea21-4953-89f9-0e20aff9eb73",
        "new orleans": "0d855753-ea21-4953-89f9-0e20aff9eb73",
        "new orleans saints": "0d855753-ea21-4953-89f9-0e20aff9eb73",
        "buccaneers": "4254d319-1bc7-4f81-b4ab-b5c0b9db8cf9",
        "tampa bay": "4254d319-1bc7-4f81-b4ab-b5c0b9db8cf9",
        "tampa bay buccaneers": "4254d319-1bc7-4f81-b4ab-b5c0b9db8cf9",
        
        # NFC West
        "cardinals": "de760528-1dc0-416a-a978-b510d20692ff",
        "arizona": "de760528-1dc0-416a-a978-b510d20692ff",
        "arizona cardinals": "de760528-1dc0-416a-a978-b510d20692ff",
        "rams": "2eff2a03-54d4-46ba-890e-2bc3925548f3",
        "los angeles rams": "2eff2a03-54d4-46ba-890e-2bc3925548f3",
        "49ers": "f0e724b0-4cbf-495a-be47-013907608da9",
        "san francisco": "f0e724b0-4cbf-495a-be47-013907608da9",
        "san francisco 49ers": "f0e724b0-4cbf-495a-be47-013907608da9",
        "seahawks": "3d08af9e-c767-4f9a-8e3b-5e5e7a11c4f8",
        "seattle": "3d08af9e-c767-4f9a-8e3b-5e5e7a11c4f8",
        "seattle seahawks": "3d08af9e-c767-4f9a-8e3b-5e5e7a11c4f8",
    }
    
    # NFL position importance weights
    POSITION_WEIGHTS = {
        "QB": 0.5,   # Quarterback is most important
        "RB": 0.25,  # Running back
        "WR": 0.2,   # Wide receiver
        "TE": 0.15,  # Tight end
        "LT": 0.2,   # Left tackle (protects QB blind side)
        "RT": 0.15,  # Right tackle
        "LG": 0.1,   # Guards
        "RG": 0.1,
        "C": 0.1,    # Center
        "DE": 0.2,   # Defensive ends
        "DT": 0.15,  # Defensive tackles
        "LB": 0.15,  # Linebackers
        "CB": 0.2,   # Cornerbacks
        "S": 0.15,   # Safeties
        "K": 0.1,    # Kicker
        "P": 0.05,   # Punter
    }
    
    def _normalize_team_name(self, team_name: str) -> Optional[str]:
        """Convert team name to SportsRadar team ID"""
        normalized = team_name.lower().strip()
        return self.TEAM_MAP.get(normalized)
    
    def _get_position_importance(self, position: str) -> float:
        """Get importance weight for NFL position"""
        return self.POSITION_WEIGHTS.get(position.upper(), 0.1)
    
    def _parse_team_stats(self, data: Dict) -> Dict:
        """Parse NFL team statistics from SportsRadar response
        
        Handles both formats:
        - Seasonal Statistics endpoint: /seasons/{season}/{season_type}/teams/{team_id}/statistics.json
        - Team Profile endpoint: /teams/{team_id}/profile.json
        """
        # Handle seasonal statistics format (has 'statistics' key)
        if 'statistics' in data:
            stats_data = data.get('statistics', {})
            team = data.get('team', {})
            record = stats_data.get('record', {})
        else:
            # Handle team profile format
            team = data.get('team', data)
            record = data.get('record', {})
            stats_data = data
        
        # Parse overall record - handle different structures
        if isinstance(record, dict):
            overall = record.get('overall', record)
            wins = overall.get('wins', record.get('wins', 0))
            losses = overall.get('losses', record.get('losses', 0))
            ties = overall.get('ties', record.get('ties', 0))
        else:
            wins = losses = ties = 0
        
        # Parse offensive stats - check both locations
        offense_raw = stats_data.get('offense', data.get('offense', {}))
        offense = self._parse_offense_stats(offense_raw)
        
        # Parse defensive stats - check both locations
        defense_raw = stats_data.get('defense', data.get('defense', {}))
        defense = self._parse_defense_stats(defense_raw)
        
        # Calculate efficiency metrics
        games_played = wins + losses + ties
        ppg = offense.get('points_per_game', 0)
        papg = defense.get('points_allowed_per_game', 0)
        
        # Extract team name from various possible locations
        team_name = (
            team.get('name') or 
            team.get('market') or 
            data.get('name') or 
            ''
        )
        team_abbr = team.get('alias') or team.get('abbreviation') or ''
        
        return {
            'name': team_name,
            'abbreviation': team_abbr,
            'record': {
                'wins': wins,
                'losses': losses,
                'ties': ties,
                'win_percentage': wins / games_played if games_played > 0 else 0,
            },
            'offense': offense,
            'defense': defense,
            'efficiency': {
                'point_differential': ppg - papg,
                'offensive_efficiency': self._calculate_offensive_efficiency(offense),
                'defensive_efficiency': self._calculate_defensive_efficiency(defense),
            },
            'situational': {
                'home_record': self._parse_split_record(record.get('home', {})) if isinstance(record, dict) else "0-0",
                'away_record': self._parse_split_record(record.get('away', {})) if isinstance(record, dict) else "0-0",
                'division_record': self._parse_split_record(record.get('division', {})) if isinstance(record, dict) else "0-0",
            }
        }
    
    def _parse_offense_stats(self, offense: Dict) -> Dict:
        """Parse offensive statistics"""
        passing = offense.get('passing', {})
        rushing = offense.get('rushing', {})
        receiving = offense.get('receiving', {})
        
        return {
            'points_per_game': offense.get('points_per_game', 0),
            'total_yards_per_game': offense.get('yards_per_game', 0),
            'passing': {
                'yards_per_game': passing.get('yards_per_game', 0),
                'touchdowns': passing.get('touchdowns', 0),
                'interceptions': passing.get('interceptions', 0),
                'completion_pct': passing.get('completion_pct', 0),
                'passer_rating': passing.get('rating', 0),
            },
            'rushing': {
                'yards_per_game': rushing.get('yards_per_game', 0),
                'touchdowns': rushing.get('touchdowns', 0),
                'yards_per_carry': rushing.get('avg_yards', 0),
            },
            'third_down_pct': offense.get('third_down_pct', 0),
            'red_zone_pct': offense.get('red_zone_pct', 0),
            'turnovers': offense.get('turnovers', 0),
        }
    
    def _parse_defense_stats(self, defense: Dict) -> Dict:
        """Parse defensive statistics"""
        passing = defense.get('passing', {})
        rushing = defense.get('rushing', {})
        
        return {
            'points_allowed_per_game': defense.get('points_per_game', 0),
            'yards_allowed_per_game': defense.get('yards_per_game', 0),
            'passing_allowed': {
                'yards_per_game': passing.get('yards_per_game', 0),
                'touchdowns_allowed': passing.get('touchdowns', 0),
                'interceptions': passing.get('interceptions', 0),
            },
            'rushing_allowed': {
                'yards_per_game': rushing.get('yards_per_game', 0),
                'touchdowns_allowed': rushing.get('touchdowns', 0),
            },
            'sacks': defense.get('sacks', 0),
            'takeaways': defense.get('takeaways', 0),
            'third_down_stop_pct': 100 - defense.get('third_down_pct', 50),
        }
    
    def _parse_split_record(self, split: Dict) -> Dict:
        """Parse a record split (home/away/division)"""
        return {
            'wins': split.get('wins', 0),
            'losses': split.get('losses', 0),
            'ties': split.get('ties', 0),
        }
    
    def _calculate_offensive_efficiency(self, offense: Dict) -> float:
        """
        Calculate offensive efficiency score (0-100).
        Based on points, yards, turnovers, and conversion rates.
        """
        # Weights for different factors
        ppg_score = min(100, (offense.get('points_per_game', 0) / 35) * 100)
        ypg_score = min(100, (offense.get('total_yards_per_game', 0) / 400) * 100)
        third_down = offense.get('third_down_pct', 40)
        red_zone = offense.get('red_zone_pct', 50)
        
        # Penalty for turnovers (assume 2 per game is average)
        to_penalty = max(0, (offense.get('turnovers', 0) - 2) * 5)
        
        efficiency = (ppg_score * 0.35 + ypg_score * 0.25 + 
                     third_down * 0.2 + red_zone * 0.2 - to_penalty)
        
        return round(max(0, min(100, efficiency)), 1)
    
    def _calculate_defensive_efficiency(self, defense: Dict) -> float:
        """
        Calculate defensive efficiency score (0-100).
        Lower points/yards allowed = higher score.
        """
        # Inverse scoring - lower is better for defense
        papg = defense.get('points_allowed_per_game', 25)
        yapg = defense.get('yards_allowed_per_game', 350)
        
        papg_score = max(0, 100 - (papg / 35) * 100)
        yapg_score = max(0, 100 - (yapg / 400) * 100)
        
        # Bonus for takeaways and sacks
        takeaway_bonus = min(20, defense.get('takeaways', 0) * 2)
        sack_bonus = min(10, defense.get('sacks', 0))
        
        efficiency = (papg_score * 0.4 + yapg_score * 0.3 + 
                     takeaway_bonus + sack_bonus)
        
        return round(max(0, min(100, efficiency)), 1)


# Factory function for easy import
@lru_cache(maxsize=1)
def get_nfl_fetcher() -> SportsRadarNFL:
    """Get an instance of the NFL SportsRadar fetcher"""
    return SportsRadarNFL()

