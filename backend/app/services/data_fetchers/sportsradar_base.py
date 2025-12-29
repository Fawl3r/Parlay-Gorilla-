"""
SportsRadar API Base Client

Provides common functionality for all SportsRadar sport-specific fetchers.
Includes authentication, rate limiting, and response parsing.
"""

import httpx
from typing import Dict, Optional, Any, List
from datetime import datetime, date
import logging
from abc import ABC, abstractmethod

from app.core.config import settings
from app.services.data_fetchers.fetch_utils import RateLimitedFetcher
from app.services.data_fetchers.provider_cooldown import provider_cooldowns

logger = logging.getLogger(__name__)


class SportsRadarBase(RateLimitedFetcher, ABC):
    """
    Base class for SportsRadar API clients.
    
    Each sport-specific client extends this and implements:
    - _get_base_url(): Return the API base URL for the sport
    - _get_team_endpoint(): Return endpoint for team stats
    - _parse_team_stats(): Parse team stats response
    """
    
    # SportsRadar rate limits: Trial keys are very limited (often 1 call/second or less)
    # Using conservative limits to avoid 403/429 errors
    CALLS_PER_MINUTE = 30  # Conservative: 0.5 calls/second
    CACHE_TTL_STATS = 600  # 10 minutes for stats
    CACHE_TTL_SCHEDULE = 3600  # 1 hour for schedules
    CACHE_TTL_INJURIES = 300  # 5 minutes for injuries
    # Cooldown windows when SportsRadar responds with hard limits.
    COOLDOWN_SECONDS_ON_429 = 15 * 60
    COOLDOWN_SECONDS_ON_403 = 6 * 60 * 60
    COOLDOWN_LOG_EVERY_SECONDS = 5 * 60
    
    def __init__(self, sport_code: str):
        super().__init__(
            calls_per_minute=self.CALLS_PER_MINUTE,
            cache_ttl_seconds=self.CACHE_TTL_STATS,
            name=f"sportsradar_{sport_code}"
        )
        self.sport_code = sport_code
        self.api_key = getattr(settings, 'sportsradar_api_key', None)
        self.timeout = 15.0
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Return the base URL for this sport's API"""
        pass
    
    @abstractmethod
    def _normalize_team_name(self, team_name: str) -> Optional[str]:
        """Convert team name to SportsRadar team ID or abbreviation"""
        pass
    
    @abstractmethod
    def _parse_team_stats(self, data: Dict) -> Dict:
        """Parse team statistics from API response"""
        pass
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make an authenticated request to SportsRadar API.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Optional query parameters
        
        Returns:
            JSON response or None on error
        """
        if provider_cooldowns.is_active(key=self.name):
            if provider_cooldowns.should_log(key=self.name, min_interval_seconds=self.COOLDOWN_LOG_EVERY_SECONDS):
                remaining = provider_cooldowns.remaining_seconds(key=self.name)
                reason = provider_cooldowns.reason(key=self.name) or "cooldown"
                logger.warning(
                    f"[{self.name}] Provider cooldown active ({reason}). Skipping SportsRadar requests for ~{remaining:.0f}s."
                )
            return None

        if not self.api_key:
            # SportsRadar is optional. Avoid spamming logs in local/dev when key isn't configured.
            logger.debug(f"[{self.name}] No API key configured; skipping SportsRadar request")
            return None
        
        url = f"{self.base_url}/{endpoint}"
        request_params = params or {}
        request_params['api_key'] = self.api_key
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=request_params)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    error_text = response.text[:500] if response.text else "No error details"
                    provider_cooldowns.start(
                        key=self.name,
                        seconds=self.COOLDOWN_SECONDS_ON_403,
                        reason="403 forbidden/quota",
                    )
                    logger.warning(
                        f"[{self.name}] 403 from SportsRadar (forbidden/quota). "
                        f"Entering cooldown for {self.COOLDOWN_SECONDS_ON_403 // 3600}h. "
                        f"Endpoint: {endpoint}. Error: {error_text}. "
                        f"Note: Trial API keys have very limited quotas; ESPN fallback will be used."
                    )
                    return None
                elif response.status_code == 404:
                    logger.debug(f"[{self.name}] Endpoint not found (404): {endpoint}. This may be normal for trial API.")
                elif response.status_code == 429:
                    provider_cooldowns.start(
                        key=self.name,
                        seconds=self.COOLDOWN_SECONDS_ON_429,
                        reason="429 rate_limited",
                    )
                    logger.warning(
                        f"[{self.name}] 429 rate-limited by SportsRadar. "
                        f"Entering cooldown for {self.COOLDOWN_SECONDS_ON_429 // 60}m. "
                        f"Endpoint: {endpoint}."
                    )
                    return None
                else:
                    error_text = response.text[:500] if response.text else "No error details"
                    logger.warning(f"[{self.name}] API error {response.status_code} for {endpoint}: {error_text}")
                    
        except httpx.TimeoutException:
            logger.warning(f"[{self.name}] Request timeout for {endpoint}")
        except Exception as e:
            logger.error(f"[{self.name}] Request error: {e}")
        
        return None
    
    async def get_team_stats(self, team_name: str, season: Optional[str] = None, season_type: str = "REG") -> Optional[Dict]:
        """
        Get current season statistics for a team.
        
        Args:
            team_name: Team name or abbreviation
            season: Season year (e.g., "2024"). If None, uses current season.
            season_type: Season type - "REG" (regular), "PRE" (preseason), "PST" (postseason)
        
        Returns:
            Parsed team statistics or None
        """
        team_id = self._normalize_team_name(team_name)
        if not team_id:
            logger.warning(f"[{self.name}] Unknown team: {team_name}")
            return None
        
        # Use current year if season not provided
        if not season:
            from datetime import datetime
            season = str(datetime.now().year)
        
        cache_key = self._make_cache_key("team_stats", team_id, season, season_type)
        
        async def fetch_stats():
            # Try seasonal statistics endpoint first (more detailed)
            # Note: This may not be available in trial version
            endpoint = f"seasons/{season}/{season_type}/teams/{team_id}/statistics.json"
            data = await self._make_request(endpoint)
            
            # Fallback to team profile if seasonal stats not available
            if not data:
                logger.debug(f"[{self.name}] Seasonal stats not available, trying team profile for {team_name}")
                endpoint = f"teams/{team_id}/profile.json"
                data = await self._make_request(endpoint)
            
            # If both fail, try to get basic info from schedule (trial version limitation)
            if not data:
                logger.debug(f"[{self.name}] Team endpoints not available (trial limitation), trying schedule for {team_name}")
                # Try to get team info from schedule - this works with trial
                schedule_data = await self._get_team_from_schedule(team_id, season)
                if schedule_data:
                    logger.info(f"[{self.name}] Got basic team info from schedule for {team_name}")
                    return schedule_data
            
            if data:
                return self._parse_team_stats(data)
            return None
    
    async def _get_team_from_schedule(self, team_id: str, season: str) -> Optional[Dict]:
        """
        Get basic team information from schedule endpoint.
        This works with trial keys when team profile/statistics endpoints don't.
        """
        try:
            # Get full season schedule
            endpoint = f"games/{season}/REG/schedule.json"
            data = await self._make_request(endpoint)
            
            if not data or 'weeks' not in data:
                return None
            
            # Search through games to find this team and extract basic stats
            team_games = []
            for week in data.get('weeks', []):
                for game in week.get('games', []):
                    home = game.get('home', {})
                    away = game.get('away', {})
                    
                    if home.get('id') == team_id or away.get('id') == team_id:
                        team_games.append({
                            'game': game,
                            'is_home': home.get('id') == team_id,
                            'team_data': home if home.get('id') == team_id else away,
                            'opponent': away if home.get('id') == team_id else home,
                        })
            
            if not team_games:
                return None
            
            # Extract basic info from first game (team name, etc.)
            first_game = team_games[0]
            team_data = first_game['team_data']
            
            # Return minimal structure - schedule doesn't have detailed stats
            return {
                'name': team_data.get('name', ''),
                'abbreviation': team_data.get('alias', ''),
                'record': {
                    'wins': 0,  # Can't get from schedule alone
                    'losses': 0,
                    'ties': 0,
                    'win_percentage': 0.0,
                },
                'offense': {},  # No stats available from schedule
                'defense': {},
                'note': 'Limited data from schedule endpoint (trial version)'
            }
        except Exception as e:
            logger.debug(f"[{self.name}] Error getting team from schedule: {e}")
            return None
        
        return await self.fetch_with_fallback(
            cache_key=cache_key,
            primary_fn=fetch_stats,
            cache_ttl=self.CACHE_TTL_STATS
        )
    
    async def get_schedule(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Get game schedule for a date range.
        
        Args:
            start_date: Start of date range (default: today)
            end_date: End of date range (default: 7 days from now)
        
        Returns:
            List of scheduled games
        """
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date
        
        cache_key = self._make_cache_key("schedule", str(start_date), str(end_date))
        
        async def fetch_schedule():
            # Format depends on sport, override in subclass if needed
            endpoint = f"games/{start_date.year}/{start_date.month}/{start_date.day}/schedule.json"
            data = await self._make_request(endpoint)
            if data:
                return self._parse_schedule(data)
            return []
        
        result = await self.fetch_with_fallback(
            cache_key=cache_key,
            primary_fn=fetch_schedule,
            cache_ttl=self.CACHE_TTL_SCHEDULE
        )
        return result or []
    
    def _parse_schedule(self, data: Dict) -> List[Dict]:
        """Parse schedule response. Override in subclass for sport-specific parsing."""
        games = data.get('games', [])
        return [
            {
                'id': game.get('id'),
                'status': game.get('status'),
                'scheduled': game.get('scheduled'),
                'home_team': game.get('home', {}).get('name'),
                'away_team': game.get('away', {}).get('name'),
                'venue': game.get('venue', {}).get('name'),
            }
            for game in games
        ]
    
    async def get_injuries(self, team_name: str) -> Optional[Dict]:
        """
        Get current injury report for a team.
        
        Args:
            team_name: Team name or abbreviation
        
        Returns:
            Injury report with severity scores
        """
        team_id = self._normalize_team_name(team_name)
        if not team_id:
            return None
        
        cache_key = self._make_cache_key("injuries", team_id)
        
        async def fetch_injuries():
            endpoint = f"teams/{team_id}/injuries.json"
            data = await self._make_request(endpoint)
            if data:
                return self._parse_injuries(data)
            return None
        
        return await self.fetch_with_fallback(
            cache_key=cache_key,
            primary_fn=fetch_injuries,
            cache_ttl=self.CACHE_TTL_INJURIES
        )
    
    def _parse_injuries(self, data: Dict) -> Dict:
        """
        Parse injuries and calculate severity score.
        Override in subclass for sport-specific parsing.
        """
        players = data.get('players', [])
        
        key_players_out = []
        total_severity = 0.0
        
        for player in players:
            status = player.get('status', '').lower()
            position = player.get('position', '').upper()
            name = player.get('name', player.get('full_name', 'Unknown'))
            
            # Determine severity based on position and status
            if status in ['out', 'ir', 'injured reserve']:
                severity = self._get_position_importance(position)
                total_severity += severity
                if severity >= 0.3:  # Key player threshold
                    key_players_out.append({
                        'name': name,
                        'position': position,
                        'status': status,
                        'severity': severity
                    })
        
        # Normalize severity to 0-1 scale (cap at 5 key players worth)
        injury_severity_score = min(1.0, total_severity / 1.5)
        
        return {
            'key_players_out': key_players_out,
            'injury_severity_score': round(injury_severity_score, 3),
            'total_players_injured': len(players),
            'impact_summary': self._summarize_injury_impact(key_players_out)
        }
    
    def _get_position_importance(self, position: str) -> float:
        """
        Get importance weight for a position.
        Override in sport-specific subclass.
        """
        # Default weights - override in subclass
        return 0.1
    
    def _summarize_injury_impact(self, key_players: List[Dict]) -> str:
        """Generate a summary of injury impact"""
        if not key_players:
            return "No significant injuries reported"
        
        if len(key_players) == 1:
            p = key_players[0]
            return f"{p['position']} {p['name']} is {p['status']}"
        
        positions = [p['position'] for p in key_players]
        return f"{len(key_players)} key players out: {', '.join(positions)}"
    
    async def get_recent_results(
        self,
        team_name: str,
        n: int = 5
    ) -> List[Dict]:
        """
        Get recent game results for a team.
        
        Args:
            team_name: Team name or abbreviation
            n: Number of recent games (default: 5)
        
        Returns:
            List of recent game results with scores
        """
        team_id = self._normalize_team_name(team_name)
        if not team_id:
            return []
        
        cache_key = self._make_cache_key("recent_results", team_id, n)
        
        async def fetch_results():
            endpoint = f"teams/{team_id}/results.json"
            data = await self._make_request(endpoint)
            if data:
                return self._parse_recent_results(data, n)
            return []
        
        result = await self.fetch_with_fallback(
            cache_key=cache_key,
            primary_fn=fetch_results,
            cache_ttl=self.CACHE_TTL_STATS
        )
        return result or []
    
    def _parse_recent_results(self, data: Dict, n: int) -> List[Dict]:
        """Parse recent game results. Override for sport-specific parsing."""
        games = data.get('games', data.get('results', []))[:n]
        
        results = []
        for game in games:
            home = game.get('home', {})
            away = game.get('away', {})
            
            results.append({
                'date': game.get('scheduled', game.get('date')),
                'home_team': home.get('name'),
                'away_team': away.get('name'),
                'home_score': home.get('points', home.get('score', 0)),
                'away_score': away.get('points', away.get('score', 0)),
                'is_win': None,  # Set by sport-specific parser
                'completed': game.get('status') == 'closed'
            })
        
        return results

