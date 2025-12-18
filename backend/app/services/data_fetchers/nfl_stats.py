"""NFL team statistics and performance data fetcher"""

import httpx
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from app.core.config import settings


class NFLStatsFetcher:
    """Fetches NFL team statistics and performance data from free sources"""
    
    def __init__(self):
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        # Keep consistent with probability engine budgets. This fetcher is used
        # for heuristics only; prefer fast fallback over hanging requests.
        self.timeout = float(getattr(settings, "probability_external_fetch_timeout_seconds", 2.5) or 2.5)
    
    async def get_team_stats(self, team_name: str) -> Optional[Dict]:
        """
        Get current season statistics for a team
        
        Args:
            team_name: Team name (e.g., "Ravens", "Chiefs")
            
        Returns:
            Dictionary with team stats or None if not found
        """
        try:
            # ESPN API uses team abbreviations, need to map names
            team_abbr = self._normalize_team_name(team_name)
            if not team_abbr:
                return None
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get team info and stats
                url = f"{self.base_url}/teams/{team_abbr}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_team_data(data)
                    
        except Exception as e:
            print(f"Error fetching team stats for {team_name}: {e}")
            return None
    
    async def get_recent_form(self, team_name: str, games: int = 5) -> List[Dict]:
        """
        Get recent game results for a team
        
        Args:
            team_name: Team name
            games: Number of recent games to fetch (default: 5)
            
        Returns:
            List of recent game results
        """
        try:
            team_abbr = self._normalize_team_name(team_name)
            if not team_abbr:
                return []
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get team schedule/results
                url = f"{self.base_url}/teams/{team_abbr}/schedule"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_recent_games(data, games)
                    
        except Exception as e:
            print(f"Error fetching recent form for {team_name}: {e}")
            return []
    
    async def get_head_to_head(self, team1: str, team2: str) -> Optional[Dict]:
        """
        Get head-to-head record between two teams
        
        Args:
            team1: First team name
            team2: Second team name
            
        Returns:
            Dictionary with H2H record or None
        """
        try:
            # For H2H, we'll use recent games and filter
            team1_games = await self.get_recent_form(team1, games=20)
            team2_games = await self.get_recent_form(team2, games=20)
            
            # Find common opponents or direct matchups
            h2h_games = []
            for game in team1_games:
                opponent = game.get("opponent", "").lower()
                if team2.lower() in opponent or opponent in team2.lower():
                    h2h_games.append(game)
            
            if h2h_games:
                wins = sum(1 for g in h2h_games if g.get("result") == "W")
                return {
                    "team1": team1,
                    "team2": team2,
                    "games": len(h2h_games),
                    "team1_wins": wins,
                    "team2_wins": len(h2h_games) - wins,
                }
            
            return None
            
        except Exception as e:
            print(f"Error fetching H2H for {team1} vs {team2}: {e}")
            return None
    
    def _normalize_team_name(self, team_name: str) -> Optional[str]:
        """Convert team name to ESPN API abbreviation"""
        # ESPN uses abbreviations like "BAL", "KC", etc.
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
    
    def _parse_team_data(self, data: Dict) -> Dict:
        """Parse ESPN team data into our format"""
        try:
            team = data.get("team", {})
            record = team.get("record", {})
            stats = team.get("statistics", [])
            
            return {
                "name": team.get("displayName", ""),
                "abbreviation": team.get("abbreviation", ""),
                "wins": record.get("items", [{}])[0].get("value", 0) if record.get("items") else 0,
                "losses": record.get("items", [{}])[1].get("value", 0) if record.get("items") and len(record.get("items", [])) > 1 else 0,
                "ties": record.get("items", [{}])[2].get("value", 0) if record.get("items") and len(record.get("items", [])) > 2 else 0,
                "stats": self._extract_statistics(stats),
            }
        except Exception as e:
            print(f"Error parsing team data: {e}")
            return {}
    
    def _extract_statistics(self, stats: List) -> Dict:
        """Extract key statistics from ESPN data"""
        stats_dict = {}
        for stat_group in stats:
            name = stat_group.get("name", "")
            if name in ["offense", "defense", "specialTeams"]:
                categories = stat_group.get("categories", [])
                for cat in categories:
                    cat_name = cat.get("name", "")
                    for stat in cat.get("stats", []):
                        stat_name = stat.get("name", "")
                        value = stat.get("value", 0)
                        stats_dict[f"{cat_name}_{stat_name}"] = value
        return stats_dict
    
    def _parse_recent_games(self, data: Dict, games: int) -> List[Dict]:
        """Parse recent games from schedule data"""
        try:
            events = data.get("events", [])
            recent_games = []
            
            for event in events[:games]:
                competitions = event.get("competitions", [])
                if competitions:
                    comp = competitions[0]
                    competitors = comp.get("competitors", [])
                    
                    if len(competitors) >= 2:
                        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
                        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
                        
                        if home and away:
                            recent_games.append({
                                "date": comp.get("date", ""),
                                "home_team": home.get("team", {}).get("displayName", ""),
                                "away_team": away.get("team", {}).get("displayName", ""),
                                "home_score": home.get("score", 0),
                                "away_score": away.get("score", 0),
                                "completed": comp.get("status", {}).get("type", {}).get("completed", False),
                            })
            
            return recent_games
            
        except Exception as e:
            print(f"Error parsing recent games: {e}")
            return []

