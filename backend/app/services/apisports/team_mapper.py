"""
Team Name to API-Sports Team ID Mapper

Maps Parlay Gorilla team names (from The Odds API) to API-Sports team IDs.
Uses TeamNameNormalizer for fuzzy matching and handles team name variations.

API-Sports team IDs are integers. This mapper supports:
- NFL (americanfootball_nfl)
- NBA (basketball_nba)
- NHL (icehockey_nhl)
- MLB (baseball_mlb)
- Soccer (football) - EPL, MLS, La Liga, etc.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict

from app.services.team_name_normalizer import TeamNameNormalizer

logger = logging.getLogger(__name__)

# API-Sports sport keys
SPORT_KEY_NFL = "americanfootball_nfl"
SPORT_KEY_NBA = "basketball_nba"
SPORT_KEY_NHL = "icehockey_nhl"
SPORT_KEY_MLB = "baseball_mlb"
SPORT_KEY_FOOTBALL = "football"  # Soccer

# Team name -> API-Sports team ID mappings
# These will be populated from API-Sports fixtures/standings or manually
# Format: normalized_team_name -> team_id (int)

TEAM_NAME_TO_ID: Dict[str, Dict[str, int]] = {
    SPORT_KEY_NFL: {
        # NFL teams - to be populated from API-Sports data
        # Example structure (actual IDs need to be fetched from API-Sports):
        # "baltimore ravens": 1,
        # "buffalo bills": 2,
        # etc.
    },
    SPORT_KEY_NBA: {
        # NBA teams - to be populated from API-Sports data
    },
    SPORT_KEY_NHL: {
        # NHL teams - to be populated from API-Sports data
    },
    SPORT_KEY_MLB: {
        # MLB teams - to be populated from API-Sports data
    },
    SPORT_KEY_FOOTBALL: {
        # Soccer teams - to be populated from API-Sports data
        # Organized by league (EPL, MLS, La Liga, etc.)
    },
}

# Reverse mapping: team_id -> normalized team name (for lookups)
TEAM_ID_TO_NAME: Dict[str, Dict[int, str]] = {
    SPORT_KEY_NFL: {},
    SPORT_KEY_NBA: {},
    SPORT_KEY_NHL: {},
    SPORT_KEY_MLB: {},
    SPORT_KEY_FOOTBALL: {},
}


class ApiSportsTeamMapper:
    """
    Maps team names to API-Sports team IDs.
    
    Uses TeamNameNormalizer for fuzzy matching and handles variations
    like "Los Angeles Chargers" vs "LA Chargers".
    """
    
    def __init__(self):
        self._normalizer = TeamNameNormalizer()
    
    def get_team_id(
        self,
        team_name: str,
        sport: str,
        league_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Get API-Sports team ID for a team name.
        
        Args:
            team_name: Team name from The Odds API or other source
            sport: Sport key (e.g., "americanfootball_nfl", "basketball_nba")
            league_id: Optional league ID for soccer (e.g., 39 for EPL, 253 for MLS)
        
        Returns:
            API-Sports team ID (int) or None if not found
        """
        if not team_name or not sport:
            return None
        
        # Normalize sport key
        sport_key = self._normalize_sport_key(sport)
        if sport_key not in TEAM_NAME_TO_ID:
            logger.warning(f"Unsupported sport for team mapping: {sport} (normalized: {sport_key})")
            return None
        
        # Normalize team name
        normalized = self._normalizer.normalize(team_name, sport=sport)
        if not normalized:
            return None
        
        # Try exact match first
        team_map = TEAM_NAME_TO_ID.get(sport_key, {})
        team_id = team_map.get(normalized)
        if team_id:
            return team_id
        
        # Try fuzzy matching (check if normalized name contains key or vice versa)
        for mapped_name, mapped_id in team_map.items():
            if normalized == mapped_name:
                return mapped_id
            # Check if one contains the other (for variations)
            if normalized in mapped_name or mapped_name in normalized:
                logger.debug(f"Fuzzy match: '{team_name}' -> '{mapped_name}' (ID: {mapped_id})")
                return mapped_id
        
        logger.debug(f"No team ID found for '{team_name}' (normalized: '{normalized}') in sport '{sport_key}'")
        return None
    
    def get_team_name(
        self,
        team_id: int,
        sport: str
    ) -> Optional[str]:
        """
        Get normalized team name from API-Sports team ID.
        
        Args:
            team_id: API-Sports team ID
            sport: Sport key
        
        Returns:
            Normalized team name or None if not found
        """
        if not team_id or not sport:
            return None
        
        sport_key = self._normalize_sport_key(sport)
        team_map = TEAM_ID_TO_NAME.get(sport_key, {})
        return team_map.get(team_id)
    
    def add_mapping(
        self,
        team_name: str,
        team_id: int,
        sport: str
    ) -> None:
        """
        Add or update a team name -> ID mapping.
        
        Args:
            team_name: Team name
            team_id: API-Sports team ID
            sport: Sport key
        """
        if not team_name or not team_id or not sport:
            return
        
        sport_key = self._normalize_sport_key(sport)
        if sport_key not in TEAM_NAME_TO_ID:
            logger.warning(f"Cannot add mapping for unsupported sport: {sport_key}")
            return
        
        normalized = self._normalizer.normalize(team_name, sport=sport)
        if not normalized:
            return
        
        TEAM_NAME_TO_ID[sport_key][normalized] = team_id
        TEAM_ID_TO_NAME[sport_key][team_id] = normalized
        
        logger.debug(f"Added mapping: '{team_name}' (normalized: '{normalized}') -> {team_id} for {sport_key}")
    
    def populate_from_fixtures(
        self,
        fixtures: list[dict],
        sport: str,
        league_id: Optional[int] = None
    ) -> int:
        """
        Populate team mappings from API-Sports fixtures data.
        
        Args:
            fixtures: List of fixture dicts from API-Sports
            sport: Sport key
            league_id: Optional league ID
        
        Returns:
            Number of mappings added
        """
        count = 0
        sport_key = self._normalize_sport_key(sport)
        
        for fixture in fixtures:
            teams = fixture.get("teams", {})
            if not isinstance(teams, dict):
                continue
            
            home_team = teams.get("home", {})
            away_team = teams.get("away", {})
            
            if isinstance(home_team, dict):
                team_id = home_team.get("id")
                team_name = home_team.get("name")
                if team_id and team_name:
                    self.add_mapping(team_name, team_id, sport)
                    count += 1
            
            if isinstance(away_team, dict):
                team_id = away_team.get("id")
                team_name = away_team.get("name")
                if team_id and team_name:
                    self.add_mapping(team_name, team_id, sport)
                    count += 1
        
        logger.info(f"Populated {count} team mappings from fixtures for {sport_key}")
        return count
    
    def populate_from_standings(
        self,
        standings: list[dict],
        sport: str,
        league_id: Optional[int] = None
    ) -> int:
        """
        Populate team mappings from API-Sports standings data.
        
        Args:
            standings: List of standings dicts from API-Sports
            sport: Sport key
            league_id: Optional league ID
        
        Returns:
            Number of mappings added
        """
        count = 0
        sport_key = self._normalize_sport_key(sport)
        
        # Standings structure varies by sport
        # For football (soccer), it's typically: standings[0]["league"]["standings"][0] -> list of teams
        # For NBA/NHL/MLB, it might be different
        
        for standing_group in standings:
            if not isinstance(standing_group, dict):
                continue
            
            # Try different possible structures
            league_data = standing_group.get("league", {})
            if league_data:
                standings_list = league_data.get("standings", [])
                if standings_list and isinstance(standings_list[0], list):
                    # Soccer format: standings is a list of lists (by group/division)
                    for group in standings_list:
                        for team_data in group:
                            if isinstance(team_data, dict):
                                team_id = team_data.get("team", {}).get("id") if isinstance(team_data.get("team"), dict) else team_data.get("id")
                                team_name = team_data.get("team", {}).get("name") if isinstance(team_data.get("team"), dict) else team_data.get("name")
                                if team_id and team_name:
                                    self.add_mapping(team_name, team_id, sport)
                                    count += 1
                elif isinstance(standings_list, list):
                    # Direct list format
                    for team_data in standings_list:
                        if isinstance(team_data, dict):
                            team_id = team_data.get("team", {}).get("id") if isinstance(team_data.get("team"), dict) else team_data.get("id")
                            team_name = team_data.get("team", {}).get("name") if isinstance(team_data.get("team"), dict) else team_data.get("name")
                            if team_id and team_name:
                                self.add_mapping(team_name, team_id, sport)
                                count += 1
            
            # Also try direct team entries
            team_id = standing_group.get("team", {}).get("id") if isinstance(standing_group.get("team"), dict) else standing_group.get("id")
            team_name = standing_group.get("team", {}).get("name") if isinstance(standing_group.get("team"), dict) else standing_group.get("name")
            if team_id and team_name:
                self.add_mapping(team_name, team_id, sport)
                count += 1
        
        logger.info(f"Populated {count} team mappings from standings for {sport_key}")
        return count
    
    def _normalize_sport_key(self, sport: str) -> str:
        """
        Normalize sport identifier to API-Sports sport key.
        
        Args:
            sport: Sport identifier (e.g., "nfl", "NFL", "americanfootball_nfl")
        
        Returns:
            Normalized sport key
        """
        sport_lower = sport.lower().strip()
        
        # Map common variations to API-Sports keys.
        # "football" = soccer (SPORT_KEY_FOOTBALL); American football must be explicit (nfl, americanfootball_nfl).
        sport_map = {
            "nfl": SPORT_KEY_NFL,
            "americanfootball_nfl": SPORT_KEY_NFL,
            "americanfootball": SPORT_KEY_NFL,
            "football": SPORT_KEY_FOOTBALL,  # Soccer
            "nba": SPORT_KEY_NBA,
            "basketball_nba": SPORT_KEY_NBA,
            "basketball": SPORT_KEY_NBA,
            "nhl": SPORT_KEY_NHL,
            "icehockey_nhl": SPORT_KEY_NHL,
            "icehockey": SPORT_KEY_NHL,
            "hockey": SPORT_KEY_NHL,
            "mlb": SPORT_KEY_MLB,
            "baseball_mlb": SPORT_KEY_MLB,
            "baseball": SPORT_KEY_MLB,
            "soccer": SPORT_KEY_FOOTBALL,
            "football_soccer": SPORT_KEY_FOOTBALL,
            "epl": SPORT_KEY_FOOTBALL,
            "mls": SPORT_KEY_FOOTBALL,
            "laliga": SPORT_KEY_FOOTBALL,
            "la liga": SPORT_KEY_FOOTBALL,
            "bundesliga": SPORT_KEY_FOOTBALL,
            "serie a": SPORT_KEY_FOOTBALL,
            "ligue 1": SPORT_KEY_FOOTBALL,
        }
        
        return sport_map.get(sport_lower, sport_lower)


# Singleton instance
_team_mapper: Optional[ApiSportsTeamMapper] = None


def get_team_mapper() -> ApiSportsTeamMapper:
    """Get singleton instance of ApiSportsTeamMapper."""
    global _team_mapper
    if _team_mapper is None:
        _team_mapper = ApiSportsTeamMapper()
    return _team_mapper
