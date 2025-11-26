"""NFL injury report data fetcher"""

import httpx
from typing import Dict, List, Optional
from datetime import datetime
from app.core.config import settings


class InjuryFetcher:
    """Fetches NFL injury reports from free sources"""
    
    def __init__(self):
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.timeout = 10.0
    
    async def get_team_injuries(self, team_name: str) -> List[Dict]:
        """
        Get current injury report for a team
        
        Args:
            team_name: Team name
            
        Returns:
            List of injured players with status
        """
        try:
            team_abbr = self._normalize_team_name(team_name)
            if not team_abbr:
                return []
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # ESPN API endpoint for injuries
                url = f"{self.base_url}/teams/{team_abbr}/injuries"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_injury_data(data)
                else:
                    # Fallback: try alternative endpoint
                    return await self._get_injuries_alternative(team_abbr)
                    
        except Exception as e:
            print(f"Error fetching injuries for {team_name}: {e}")
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
        
        key_positions = ["QB", "RB", "WR", "TE", "OL"] if not position else [position]
        key_players = {}
        
        for injury in injuries:
            player_pos = injury.get("position", "")
            if any(pos in player_pos for pos in key_positions):
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

