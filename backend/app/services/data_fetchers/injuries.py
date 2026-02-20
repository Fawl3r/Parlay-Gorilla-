"""Injury data fetcher with multi-sport ESPN team resolution."""

import httpx
from typing import Dict, List, Optional
from app.core.config import settings
from app.services.espn.espn_injuries_client import EspnInjuriesClient
from app.services.espn.espn_team_resolver import EspnTeamResolver


class InjuryFetcher:
    """Fetches injury reports across sports using ESPN team-ID resolution."""

    SPORT_CODE_MAP = {
        "nfl": "nfl",
        "americanfootball_nfl": "nfl",
        "nba": "nba",
        "basketball_nba": "nba",
        "wnba": "wnba",
        "basketball_wnba": "wnba",
        "nhl": "nhl",
        "icehockey_nhl": "nhl",
        "mlb": "mlb",
        "baseball_mlb": "mlb",
        "soccer": "soccer",
        "soccer_epl": "epl",
        "soccer_mls": "mls",
        "epl": "epl",
        "mls": "mls",
        "laliga": "laliga",
        "seriea": "seriea",
        "bundesliga": "bundesliga",
        "ucl": "ucl",
    }
    
    def __init__(self, sport: str = "nfl"):
        self.sport = (sport or "nfl").lower().strip()
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        # Keep consistent with probability engine budgets. This fetcher is used
        # for heuristics only; prefer fast fallback over hanging requests.
        self.timeout = float(getattr(settings, "probability_external_fetch_timeout_seconds", 2.5) or 2.5)
        self._resolver = EspnTeamResolver(timeout=self.timeout)
        self._injuries_client = EspnInjuriesClient(timeout=self.timeout)
    
    async def get_team_injuries(self, team_name: str) -> List[Dict]:
        """
        Get current injury report for a team.
        Uses ESPN team resolver for all sports; falls back to legacy NFL endpoint.
        
        Args:
            team_name: Team name
            
        Returns:
            List of injured players with status
        """
        sport_code = self._resolve_sport_code(self.sport)
        try:
            team_ref = await self._resolver.resolve_team_ref(sport_code, team_name)
            if team_ref:
                parsed = await self._injuries_client.fetch_injuries_for_team_ref(sport_code, team_ref)
                if isinstance(parsed, dict):
                    return self._coerce_canonical_injuries(parsed)
        except Exception as e:
            print(f"Error fetching injuries for {team_name}: {e}")

        # Last-resort fallback for NFL only (legacy endpoint using team abbreviation).
        if sport_code == "nfl":
            return await self._get_nfl_legacy_injuries(team_name)
        return []
    
    async def get_key_player_status(
        self,
        team_name: str,
        position: Optional[str] = None
    ) -> Dict:
        """
        Get status of key players (QB, RB1, WR1, etc.)
        
        Args:
            team_name: Team name
            position: Optional position filter (QB, RB, WR, etc.)
            
        Returns:
            Dictionary with key player statuses
        """
        injuries = await self.get_team_injuries(team_name)
        
        key_positions = self._default_key_positions(position)
        key_players = {}
        
        for injury in injuries:
            player_pos = (injury.get("position", "") or "").upper()
            # If no position is provided, still keep the player in the output.
            if player_pos and key_positions and all(pos not in player_pos for pos in key_positions):
                continue

            player_name = injury.get("player", "")
            status = injury.get("status", "")
            
            if player_name:
                key_players[player_name] = {
                    "position": player_pos,
                    "status": status,
                    "injury": injury.get("injury", ""),
                    "impact": self._assess_impact(status, player_pos),
                }
        
        return key_players

    def _resolve_sport_code(self, sport: str) -> str:
        sport_key = (sport or "").lower().strip()
        return self.SPORT_CODE_MAP.get(sport_key, "nfl")

    def _default_key_positions(self, position: Optional[str]) -> List[str]:
        if position:
            return [position.upper().strip()]

        sport_code = self._resolve_sport_code(self.sport)
        if sport_code == "nfl":
            return ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S"]
        if sport_code == "nba":
            return ["PG", "SG", "SF", "PF", "C", "G", "F"]
        if sport_code == "wnba":
            return ["PG", "SG", "SF", "PF", "C", "G", "F"]
        if sport_code == "nhl":
            return ["C", "LW", "RW", "D", "G"]
        if sport_code == "mlb":
            return ["SP", "RP", "CP", "C", "1B", "2B", "3B", "SS", "OF", "DH"]
        # Soccer and unknown leagues: keep all by default.
        return []

    def _coerce_canonical_injuries(self, parsed: Dict) -> List[Dict]:
        key_players = parsed.get("key_players_out", [])
        if not isinstance(key_players, list):
            return []

        injuries: List[Dict] = []
        for player in key_players:
            if isinstance(player, dict):
                injuries.append(
                    {
                        "player": player.get("name", ""),
                        "position": player.get("position", ""),
                        "status": player.get("status", ""),
                        "injury": player.get("description", player.get("reason", "")),
                        "date": "",
                    }
                )
            elif isinstance(player, str) and player.strip():
                injuries.append(
                    {
                        "player": player.strip(),
                        "position": "",
                        "status": "out",
                        "injury": "",
                        "date": "",
                    }
                )
        return injuries

    async def _get_nfl_legacy_injuries(self, team_name: str) -> List[Dict]:
        team_abbr = self._normalize_team_name(team_name)
        if not team_abbr:
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/teams/{team_abbr}/injuries"
                response = await client.get(url)
                if response.status_code == 200:
                    return self._parse_injury_data(response.json())
                return await self._get_injuries_alternative(team_abbr)
        except Exception:
            return []
    
    def _normalize_team_name(self, team_name: str) -> Optional[str]:
        """Convert team name to ESPN API abbreviation"""
        # Same mapping as NFLStatsFetcher
        team_map = {
            "ravens": "BAL", "baltimore": "BAL",
            "chiefs": "KC", "kansas city": "KC",
            "bills": "BUF", "buffalo": "BUF",
            "dolphins": "MIA", "miami": "MIA",
            "patriots": "NE", "new england": "NE",
            "jets": "NYJ", "new york jets": "NYJ",
            "bengals": "CIN", "cincinnati": "CIN",
            "browns": "CLE", "cleveland": "CLE",
            "steelers": "PIT", "pittsburgh": "PIT",
            "texans": "HOU", "houston": "HOU",
            "colts": "IND", "indianapolis": "IND",
            "jaguars": "JAX", "jacksonville": "JAX",
            "titans": "TEN", "tennessee": "TEN",
            "broncos": "DEN", "denver": "DEN",
            "chargers": "LAC", "los angeles chargers": "LAC",
            "raiders": "LV", "las vegas": "LV",
            "cowboys": "DAL", "dallas": "DAL",
            "giants": "NYG", "new york giants": "NYG",
            "eagles": "PHI", "philadelphia": "PHI",
            "commanders": "WAS", "washington": "WAS",
            "bears": "CHI", "chicago": "CHI",
            "lions": "DET", "detroit": "DET",
            "packers": "GB", "green bay": "GB",
            "vikings": "MIN", "minnesota": "MIN",
            "falcons": "ATL", "atlanta": "ATL",
            "panthers": "CAR", "carolina": "CAR",
            "saints": "NO", "new orleans": "NO",
            "buccaneers": "TB", "tampa bay": "TB",
            "cardinals": "ARI", "arizona": "ARI",
            "rams": "LAR", "los angeles rams": "LAR",
            "49ers": "SF", "san francisco": "SF",
            "seahawks": "SEA", "seattle": "SEA",
        }
        
        team_lower = team_name.lower().strip()
        return team_map.get(team_lower)
    
    def _parse_injury_data(self, data: Dict) -> List[Dict]:
        """Parse ESPN injury data"""
        try:
            injuries = []
            # ESPN API structure may vary
            athletes = data.get("athletes", [])
            
            for athlete in athletes:
                injury_info = athlete.get("injury", {})
                status = injury_info.get("status", "")
                
                if status:  # Only include if there's an injury status
                    injuries.append({
                        "player": athlete.get("fullName", ""),
                        "position": athlete.get("position", {}).get("abbreviation", ""),
                        "status": status,
                        "injury": injury_info.get("type", ""),
                        "date": injury_info.get("date", ""),
                    })
            
            return injuries
            
        except Exception as e:
            print(f"Error parsing injury data: {e}")
            return []
    
    async def _get_injuries_alternative(self, team_abbr: str) -> List[Dict]:
        """Alternative method to get injuries if primary fails"""
        # Could scrape or use other free sources
        # For now, return empty list
        return []
    
    def _assess_impact(self, status: str, position: str) -> str:
        """
        Assess impact level of injury
        
        Returns: "high", "medium", "low", or "none"
        """
        status_lower = status.lower()
        
        # High impact statuses
        if any(term in status_lower for term in ["out", "doubtful", "ir", "pup"]):
            return "high"
        
        # Medium impact
        if any(term in status_lower for term in ["questionable", "limited"]):
            return "medium"
        
        # Low impact
        if any(term in status_lower for term in ["probable", "full"]):
            return "low"
        
        return "none"

