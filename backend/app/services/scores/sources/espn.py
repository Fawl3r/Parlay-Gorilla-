"""ESPN scoreboard scraper."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urlencode

import httpx
from bs4 import BeautifulSoup

from app.services.scores.normalizer import GameUpdate, ScoreNormalizer

logger = logging.getLogger(__name__)


class ESPNScraper:
    """Scraper for ESPN scoreboard data."""
    
    BASE_URL = "https://www.espn.com"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    def __init__(self):
        self._normalizer = ScoreNormalizer()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=10.0,
                headers={"User-Agent": self.USER_AGENT},
                follow_redirects=True,
            )
        return self._client
    
    async def close(self):
        """Close the client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    def _get_sport_path(self, sport: str) -> str:
        """Map sport code to ESPN path."""
        sport_map = {
            "NFL": "nfl",
            "NBA": "nba",
            "NHL": "nhl",
            "MLB": "mlb",
            "NCAAF": "college-football",
            "NCAAB": "mens-college-basketball",
        }
        return sport_map.get(sport.upper(), sport.lower())
    
    async def fetch_scoreboard(self, sport: str, date: datetime) -> List[GameUpdate]:
        """Fetch scoreboard for a sport and date.
        
        Args:
            sport: Sport code (NFL, NBA, etc.)
            date: Date to fetch games for
            
        Returns:
            List of GameUpdate objects
        """
        try:
            sport_path = self._get_sport_path(sport)
            date_str = date.strftime("%Y%m%d")
            
            # Try ESPN API endpoint first (often available as JSON)
            api_url = f"{self.BASE_URL}/{sport_path}/scoreboard/_/date/{date_str}"
            
            client = await self._get_client()
            
            try:
                response = await client.get(api_url)
                if response.status_code == 200:
                    # Try to parse as JSON first
                    try:
                        data = response.json()
                        return self._parse_json_scoreboard(data, sport, date)
                    except Exception:
                        # Fall back to HTML parsing
                        html = response.text
                        return self._parse_html_scoreboard(html, sport, date)
                return []
            except httpx.TimeoutException:
                logger.warning(f"ESPN timeout for {sport} on {date_str}")
                return []
            except Exception as e:
                logger.error(f"ESPN fetch error for {sport} on {date_str}: {e}")
                return []
        
        except Exception as e:
            logger.error(f"ESPN scraper error: {e}")
            return []
    
    def _parse_json_scoreboard(self, data: dict, sport: str, date: datetime) -> List[GameUpdate]:
        """Parse ESPN JSON scoreboard response."""
        games = []
        
        try:
            # ESPN JSON structure varies, but typically has 'events' or 'games'
            scoreboard = data.get("scoreboard") if isinstance(data.get("scoreboard"), dict) else {}
            events = data.get("events") or data.get("games") or scoreboard.get("events") or []
            if not isinstance(events, list):
                events = []

            for event in events:
                try:
                    game_update = self._parse_event(event, sport, date)
                    if game_update:
                        games.append(game_update)
                except Exception as e:
                    logger.debug(f"Error parsing ESPN event: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing ESPN JSON: {e}")
        
        return games
    
    def _parse_html_scoreboard(self, html: str, sport: str, date: datetime) -> List[GameUpdate]:
        """Parse ESPN HTML scoreboard page."""
        games = []
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # ESPN HTML structure varies, but typically has game cards
            # Look for common patterns: game-card, ScoreboardGame, etc.
            game_elements = soup.find_all(["div", "section"], class_=lambda x: x and ("game" in x.lower() or "score" in x.lower()))
            
            for element in game_elements:
                try:
                    game_update = self._parse_html_game(element, sport, date)
                    if game_update:
                        games.append(game_update)
                except Exception as e:
                    logger.debug(f"Error parsing ESPN HTML game: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing ESPN HTML: {e}")
        
        return games
    
    def _parse_event(self, event: dict, sport: str, date: datetime) -> Optional[GameUpdate]:
        """Parse a single event from ESPN JSON."""
        try:
            # Extract teams
            competitors = event.get("competitions", [{}])[0].get("competitors", [])
            if len(competitors) < 2:
                return None
            
            home_comp = next((c for c in competitors if c.get("homeAway") == "home"), None)
            away_comp = next((c for c in competitors if c.get("homeAway") == "away"), None)
            
            if not home_comp or not away_comp:
                return None
            
            home_team = home_comp.get("team", {}).get("displayName", "") or home_comp.get("team", {}).get("name", "")
            away_team = away_comp.get("team", {}).get("displayName", "") or away_comp.get("team", {}).get("name", "")
            
            # Extract scores
            home_score = home_comp.get("score")
            away_score = away_comp.get("score")
            
            # Extract status
            status_obj = event.get("competitions", [{}])[0].get("status", {})
            raw_status = status_obj.get("type", {}).get("name", "") or status_obj.get("name", "")
            status = self._normalizer.normalize_status(raw_status, sport)
            
            # Extract period/clock
            period = status_obj.get("period", {}).get("displayName") or status_obj.get("period")
            clock = status_obj.get("clock") or status_obj.get("displayClock")
            
            # Extract start time
            start_time_str = event.get("date") or event.get("startDate")
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                except:
                    start_time = date
            else:
                start_time = date
            
            # Create external game key
            external_key = self._normalizer.create_external_game_key(home_team, away_team, start_time, sport)
            
            return GameUpdate(
                external_game_key=external_key,
                home_team=home_team,
                away_team=away_team,
                home_score=int(home_score) if home_score is not None else None,
                away_score=int(away_score) if away_score is not None else None,
                status=status,
                period=self._normalizer.normalize_period(str(period) if period else "", sport),
                clock=str(clock) if clock else None,
                start_time=start_time,
                data_source="espn",
            )
        
        except Exception as e:
            logger.debug(f"Error parsing ESPN event: {e}")
            return None
    
    def _parse_html_game(self, element, sport: str, date: datetime) -> Optional[GameUpdate]:
        """Parse a single game from ESPN HTML."""
        # This is a placeholder - actual implementation would parse HTML structure
        # ESPN HTML structure changes frequently, so this needs to be adapted
        logger.debug("ESPN HTML parsing not fully implemented - JSON preferred")
        return None
