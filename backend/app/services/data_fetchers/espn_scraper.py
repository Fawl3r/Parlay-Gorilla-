"""
ESPN Data Scraper

Fetches data from ESPN's public APIs as a fallback/supplement to SportsRadar.
Uses ESPN's undocumented but stable public API endpoints.

Provides:
- Team statistics
- Matchup context and history
- Power rankings
- Injury news with context
- Recent game results
"""

import httpx
from typing import Dict, Optional, List, Any
from datetime import datetime, date
import logging
import re

from app.services.data_fetchers.fetch_utils import RateLimitedFetcher

logger = logging.getLogger(__name__)


class ESPNScraper(RateLimitedFetcher):
    """
    ESPN data scraper using public ESPN API endpoints.
    
    Falls back gracefully when data is unavailable.
    Respects rate limits and caches aggressively.
    """
    
    # ESPN API base URLs by sport
    SPORT_URLS = {
        "nfl": "https://site.api.espn.com/apis/site/v2/sports/football/nfl",
        "nba": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba",
        "nhl": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl",
        "mlb": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb",
        "soccer_epl": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1",
        "soccer_mls": "https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1",
    }
    
    # Team name to ESPN abbreviation mapping
    NFL_TEAMS = {
        "ravens": "BAL", "baltimore": "BAL", "bills": "BUF", "buffalo": "BUF",
        "dolphins": "MIA", "miami": "MIA", "patriots": "NE", "new england": "NE",
        "jets": "NYJ", "bengals": "CIN", "cincinnati": "CIN", "browns": "CLE",
        "cleveland": "CLE", "steelers": "PIT", "pittsburgh": "PIT",
        "texans": "HOU", "houston": "HOU", "colts": "IND", "indianapolis": "IND",
        "jaguars": "JAX", "jacksonville": "JAX", "titans": "TEN", "tennessee": "TEN",
        "broncos": "DEN", "denver": "DEN", "chiefs": "KC", "kansas city": "KC",
        "raiders": "LV", "las vegas": "LV", "chargers": "LAC",
        "cowboys": "DAL", "dallas": "DAL", "giants": "NYG", "eagles": "PHI",
        "philadelphia": "PHI", "commanders": "WAS", "washington": "WAS",
        "bears": "CHI", "chicago": "CHI", "lions": "DET", "detroit": "DET",
        "packers": "GB", "green bay": "GB", "vikings": "MIN", "minnesota": "MIN",
        "falcons": "ATL", "atlanta": "ATL", "panthers": "CAR", "carolina": "CAR",
        "saints": "NO", "new orleans": "NO", "buccaneers": "TB", "tampa bay": "TB",
        "cardinals": "ARI", "arizona": "ARI", "rams": "LAR", "los angeles rams": "LAR",
        "49ers": "SF", "san francisco": "SF", "seahawks": "SEA", "seattle": "SEA",
    }
    
    NBA_TEAMS = {
        "celtics": "BOS", "boston": "BOS", "nets": "BKN", "brooklyn": "BKN",
        "knicks": "NY", "new york": "NY", "76ers": "PHI", "sixers": "PHI",
        "raptors": "TOR", "toronto": "TOR", "bulls": "CHI", "chicago": "CHI",
        "cavaliers": "CLE", "cavs": "CLE", "cleveland": "CLE",
        "pistons": "DET", "detroit": "DET", "pacers": "IND", "indiana": "IND",
        "bucks": "MIL", "milwaukee": "MIL", "hawks": "ATL", "atlanta": "ATL",
        "hornets": "CHA", "charlotte": "CHA", "heat": "MIA", "miami": "MIA",
        "magic": "ORL", "orlando": "ORL", "wizards": "WSH", "washington": "WSH",
        "nuggets": "DEN", "denver": "DEN", "timberwolves": "MIN", "minnesota": "MIN",
        "thunder": "OKC", "oklahoma city": "OKC", "trail blazers": "POR", "portland": "POR",
        "jazz": "UTA", "utah": "UTA", "warriors": "GS", "golden state": "GS",
        "clippers": "LAC", "lakers": "LAL", "los angeles lakers": "LAL",
        "suns": "PHX", "phoenix": "PHX", "kings": "SAC", "sacramento": "SAC",
        "mavericks": "DAL", "dallas": "DAL", "rockets": "HOU", "houston": "HOU",
        "grizzlies": "MEM", "memphis": "MEM", "pelicans": "NO", "new orleans": "NO",
        "spurs": "SA", "san antonio": "SA",
    }
    
    def __init__(self):
        super().__init__(
            calls_per_minute=30,  # ESPN is fairly permissive
            cache_ttl_seconds=600,  # 10 minute cache
            name="espn_scraper"
        )
        self.timeout = 10.0
    
    def _get_base_url(self, sport: str) -> str:
        """Get ESPN API base URL for a sport"""
        sport_key = sport.lower()
        if sport_key in self.SPORT_URLS:
            return self.SPORT_URLS[sport_key]
        # Check for variations
        if "soccer" in sport_key or "epl" in sport_key:
            return self.SPORT_URLS["soccer_epl"]
        if "mls" in sport_key:
            return self.SPORT_URLS["soccer_mls"]
        return self.SPORT_URLS.get("nfl")  # Default to NFL
    
    def _get_team_abbr(self, team_name: str, sport: str) -> Optional[str]:
        """Get ESPN team abbreviation"""
        normalized = team_name.lower().strip()
        
        if sport.lower() in ["nfl", "americanfootball_nfl"]:
            return self.NFL_TEAMS.get(normalized)
        elif sport.lower() in ["nba", "basketball_nba"]:
            return self.NBA_TEAMS.get(normalized)
        
        return None
    
    async def _make_request(self, url: str) -> Optional[Dict]:
        """Make an HTTP request with error handling"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"[ESPN] Request failed: {response.status_code} for {url}")
        except httpx.TimeoutException:
            logger.warning(f"[ESPN] Request timeout for {url}")
        except Exception as e:
            logger.error(f"[ESPN] Request error: {e}")
        return None
    
    async def scrape_team_stats(self, team_name: str, sport: str) -> Optional[Dict]:
        """
        Scrape team statistics from ESPN.
        
        Args:
            team_name: Team name or abbreviation
            sport: Sport code (nfl, nba, etc.)
        
        Returns:
            Team statistics dict or None
        """
        base_url = self._get_base_url(sport)
        team_abbr = self._get_team_abbr(team_name, sport)
        
        if not team_abbr:
            logger.debug(f"[ESPN] Unknown team: {team_name}")
            return None
        
        cache_key = self._make_cache_key("team_stats", sport, team_abbr)
        
        async def fetch_stats():
            url = f"{base_url}/teams/{team_abbr}"
            data = await self._make_request(url)
            if data:
                return self._parse_team_data(data, sport)
            return None
        
        return await self.fetch_with_fallback(
            cache_key=cache_key,
            primary_fn=fetch_stats
        )
    
    def _parse_team_data(self, data: Dict, sport: str) -> Dict:
        """Parse ESPN team data into standardized format"""
        team = data.get('team', {})
        record = team.get('record', {})
        stats = team.get('statistics', [])
        
        # Parse record
        items = record.get('items', [])
        wins = 0
        losses = 0
        
        for item in items:
            summary = item.get('summary', '')
            if '-' in summary:
                parts = summary.split('-')
                if len(parts) >= 2:
                    try:
                        wins = int(parts[0])
                        losses = int(parts[1])
                    except ValueError:
                        pass
        
        # Parse statistics
        parsed_stats = self._parse_statistics(stats, sport)
        
        return {
            'name': team.get('displayName', ''),
            'abbreviation': team.get('abbreviation', ''),
            'record': {
                'wins': wins,
                'losses': losses,
                'win_percentage': wins / (wins + losses) if (wins + losses) > 0 else 0,
            },
            'offense': parsed_stats.get('offense', {}),
            'defense': parsed_stats.get('defense', {}),
            'stats_raw': parsed_stats,
        }
    
    def _parse_statistics(self, stats: List, sport: str) -> Dict:
        """Parse ESPN statistics arrays"""
        result = {'offense': {}, 'defense': {}}
        
        for stat_group in stats:
            group_name = stat_group.get('name', '').lower()
            categories = stat_group.get('categories', [])
            
            for cat in categories:
                cat_name = cat.get('name', '')
                for stat in cat.get('stats', []):
                    stat_name = stat.get('name', '')
                    value = stat.get('value', 0)
                    display = stat.get('displayValue', '')
                    
                    # Categorize into offense/defense
                    if 'offense' in group_name or group_name in ['passing', 'rushing', 'receiving', 'scoring']:
                        result['offense'][f"{cat_name}_{stat_name}"] = {
                            'value': value,
                            'display': display
                        }
                    elif 'defense' in group_name:
                        result['defense'][f"{cat_name}_{stat_name}"] = {
                            'value': value,
                            'display': display
                        }
        
        return result
    
    async def scrape_matchup_context(
        self, 
        home_team: str, 
        away_team: str, 
        sport: str
    ) -> Optional[Dict]:
        """
        Scrape matchup context including head-to-head history and storylines.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            sport: Sport code
        
        Returns:
            Matchup context dict
        """
        # Get recent games for both teams to find H2H matchups
        home_games = await self.scrape_recent_games(home_team, sport, n=20)
        away_games = await self.scrape_recent_games(away_team, sport, n=20)
        
        # Find head-to-head games
        h2h_games = []
        away_lower = away_team.lower()
        home_lower = home_team.lower()
        
        for game in home_games:
            opponent = game.get('opponent', '').lower()
            if away_lower in opponent or opponent in away_lower:
                h2h_games.append(game)
        
        # Calculate H2H record
        home_wins = sum(1 for g in h2h_games if g.get('result') == 'W')
        away_wins = len(h2h_games) - home_wins
        
        return {
            'head_to_head': {
                'games': len(h2h_games),
                'home_team_wins': home_wins,
                'away_team_wins': away_wins,
                'recent_meetings': h2h_games[:5],
            },
            'home_team_form': self._calculate_form(home_games[:5]),
            'away_team_form': self._calculate_form(away_games[:5]),
            'storyline': self._generate_storyline(home_team, away_team, h2h_games, home_games, away_games),
        }
    
    def _calculate_form(self, games: List[Dict]) -> Dict:
        """Calculate recent form from games"""
        if not games:
            return {'wins': 0, 'losses': 0, 'form_string': ''}
        
        wins = sum(1 for g in games if g.get('result') == 'W')
        losses = len(games) - wins
        form_string = ''.join(['W' if g.get('result') == 'W' else 'L' for g in games])
        
        return {
            'wins': wins,
            'losses': losses,
            'win_percentage': wins / len(games) if games else 0,
            'form_string': form_string,
        }
    
    def _generate_storyline(
        self,
        home_team: str,
        away_team: str,
        h2h_games: List,
        home_games: List,
        away_games: List
    ) -> str:
        """Generate a matchup storyline based on data"""
        parts = []
        
        # H2H context
        if h2h_games:
            home_wins = sum(1 for g in h2h_games if g.get('result') == 'W')
            if home_wins > len(h2h_games) / 2:
                parts.append(f"{home_team} has won {home_wins} of the last {len(h2h_games)} meetings")
            else:
                parts.append(f"{away_team} has won {len(h2h_games) - home_wins} of the last {len(h2h_games)} meetings")
        
        # Recent form
        home_form = self._calculate_form(home_games[:5])
        away_form = self._calculate_form(away_games[:5])
        
        if home_form.get('wins', 0) >= 4:
            parts.append(f"{home_team} is on a hot streak ({home_form.get('form_string', '')})")
        elif home_form.get('wins', 0) <= 1:
            parts.append(f"{home_team} is struggling ({home_form.get('form_string', '')})")
        
        if away_form.get('wins', 0) >= 4:
            parts.append(f"{away_team} comes in hot ({away_form.get('form_string', '')})")
        elif away_form.get('wins', 0) <= 1:
            parts.append(f"{away_team} has been struggling ({away_form.get('form_string', '')})")
        
        return ". ".join(parts) + "." if parts else "First meeting of the season."
    
    async def scrape_recent_games(
        self, 
        team_name: str, 
        sport: str, 
        n: int = 5
    ) -> List[Dict]:
        """
        Scrape recent game results for a team.
        
        Args:
            team_name: Team name
            sport: Sport code
            n: Number of recent games
        
        Returns:
            List of recent game results
        """
        base_url = self._get_base_url(sport)
        team_abbr = self._get_team_abbr(team_name, sport)
        
        if not team_abbr:
            return []
        
        cache_key = self._make_cache_key("recent_games", sport, team_abbr, n)
        
        async def fetch_games():
            url = f"{base_url}/teams/{team_abbr}/schedule"
            data = await self._make_request(url)
            if data:
                return self._parse_schedule(data, team_abbr, n)
            return []
        
        result = await self.fetch_with_fallback(
            cache_key=cache_key,
            primary_fn=fetch_games
        )
        return result or []
    
    def _parse_schedule(self, data: Dict, team_abbr: str, n: int) -> List[Dict]:
        """Parse ESPN schedule data"""
        events = data.get('events', [])
        games = []
        
        for event in events:
            # Only include completed games
            status = event.get('competitions', [{}])[0].get('status', {})
            if status.get('type', {}).get('completed', False):
                competition = event.get('competitions', [{}])[0]
                competitors = competition.get('competitors', [])
                
                if len(competitors) >= 2:
                    # Find our team and opponent
                    our_team = None
                    opponent = None
                    
                    for comp in competitors:
                        if comp.get('team', {}).get('abbreviation', '') == team_abbr:
                            our_team = comp
                        else:
                            opponent = comp
                    
                    if our_team and opponent:
                        our_score = int(our_team.get('score', 0))
                        opp_score = int(opponent.get('score', 0))
                        
                        games.append({
                            'date': event.get('date', ''),
                            'opponent': opponent.get('team', {}).get('displayName', ''),
                            'opponent_abbr': opponent.get('team', {}).get('abbreviation', ''),
                            'home_away': 'home' if our_team.get('homeAway') == 'home' else 'away',
                            'our_score': our_score,
                            'opponent_score': opp_score,
                            'result': 'W' if our_score > opp_score else 'L',
                            'completed': True,
                        })
        
        return games[:n]
    
    async def scrape_power_rankings(self, sport: str) -> List[Dict]:
        """
        Scrape ESPN power rankings.
        
        Args:
            sport: Sport code
        
        Returns:
            List of teams with rankings
        """
        base_url = self._get_base_url(sport)
        cache_key = self._make_cache_key("power_rankings", sport)
        
        async def fetch_rankings():
            url = f"{base_url}/rankings"
            data = await self._make_request(url)
            if data:
                return self._parse_rankings(data)
            return []
        
        result = await self.fetch_with_fallback(
            cache_key=cache_key,
            primary_fn=fetch_rankings,
            cache_ttl=3600  # 1 hour for rankings
        )
        return result or []
    
    def _parse_rankings(self, data: Dict) -> List[Dict]:
        """Parse ESPN rankings data"""
        rankings = []
        
        for ranking in data.get('rankings', []):
            for rank_entry in ranking.get('ranks', []):
                team = rank_entry.get('team', {})
                rankings.append({
                    'rank': rank_entry.get('current', 0),
                    'previous_rank': rank_entry.get('previous', 0),
                    'team': team.get('displayName', ''),
                    'abbreviation': team.get('abbreviation', ''),
                    'record': rank_entry.get('recordSummary', ''),
                    'trend': rank_entry.get('trend', 'same'),
                })
        
        return sorted(rankings, key=lambda x: x.get('rank', 999))
    
    async def scrape_injury_news(self, team_name: str, sport: str) -> Optional[Dict]:
        """
        Scrape injury news and context for a team.
        
        Args:
            team_name: Team name
            sport: Sport code
        
        Returns:
            Injury report with context
        """
        base_url = self._get_base_url(sport)
        team_abbr = self._get_team_abbr(team_name, sport)
        
        if not team_abbr:
            return None
        
        cache_key = self._make_cache_key("injuries", sport, team_abbr)
        
        async def fetch_injuries():
            url = f"{base_url}/teams/{team_abbr}/injuries"
            data = await self._make_request(url)
            if data:
                return self._parse_injuries(data, sport)
            return None
        
        return await self.fetch_with_fallback(
            cache_key=cache_key,
            primary_fn=fetch_injuries,
            cache_ttl=300  # 5 minutes for injuries
        )
    
    def _parse_injuries(self, data: Dict, sport: str) -> Dict:
        """Parse ESPN injury data"""
        injuries = data.get('injuries', [])
        
        key_players_out = []
        total_severity = 0.0
        
        for player_injury in injuries:
            player = player_injury.get('athlete', {})
            status = player_injury.get('status', '')
            position = player.get('position', {}).get('abbreviation', '')
            name = player.get('displayName', '')
            
            # Calculate severity
            severity = self._get_injury_severity(status, position, sport)
            total_severity += severity
            
            if severity >= 0.3:  # Key player threshold
                key_players_out.append({
                    'name': name,
                    'position': position,
                    'status': status,
                    'description': player_injury.get('longComment', ''),
                    'severity': severity,
                })
        
        return {
            'key_players_out': key_players_out,
            'injury_severity_score': min(1.0, total_severity / 1.5),
            'total_injured': len(injuries),
            'summary': self._summarize_injuries(key_players_out),
        }
    
    def _get_injury_severity(self, status: str, position: str, sport: str) -> float:
        """Calculate injury severity based on status and position"""
        # Status weight
        status_weights = {
            'out': 1.0,
            'doubtful': 0.8,
            'questionable': 0.4,
            'probable': 0.1,
            'day-to-day': 0.3,
            'ir': 1.0,
        }
        status_weight = status_weights.get(status.lower(), 0.5)
        
        # Position weight (sport-specific)
        position_weights = {
            'nfl': {'QB': 0.5, 'RB': 0.25, 'WR': 0.2, 'CB': 0.2, 'LT': 0.2},
            'nba': {'PG': 0.35, 'SG': 0.25, 'SF': 0.25, 'C': 0.25},
            'nhl': {'G': 0.5, 'C': 0.3, 'D': 0.25},
            'mlb': {'SP': 0.5, 'CP': 0.25, 'SS': 0.2},
        }
        
        sport_key = sport.lower()
        if sport_key in position_weights:
            pos_weight = position_weights[sport_key].get(position.upper(), 0.1)
        else:
            pos_weight = 0.15
        
        return status_weight * pos_weight
    
    def _summarize_injuries(self, key_players: List[Dict]) -> str:
        """Generate injury summary text"""
        if not key_players:
            return "No significant injuries reported"
        
        if len(key_players) == 1:
            p = key_players[0]
            return f"{p['position']} {p['name']} is {p['status']}"
        
        positions = [p['position'] for p in key_players]
        return f"{len(key_players)} key players out: {', '.join(positions)}"


# Factory function
def get_espn_scraper() -> ESPNScraper:
    """Get an instance of the ESPN scraper"""
    return ESPNScraper()

