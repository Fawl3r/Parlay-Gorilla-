"""Yahoo Sports scoreboard scraper."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import List, Optional
import json
import re

import httpx
from bs4 import BeautifulSoup

from app.services.scores.normalizer import GameUpdate, ScoreNormalizer

logger = logging.getLogger(__name__)


class YahooScraper:
    """Scraper for Yahoo Sports scoreboard data."""
    
    BASE_URL = "https://sports.yahoo.com"
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
        """Map sport code to Yahoo path."""
        sport_map = {
            "NFL": "nfl",
            "NBA": "nba",
            "NHL": "nhl",
            "MLB": "mlb",
            "NCAAF": "ncaaf",
            "NCAAB": "ncaab",
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
            date_str = date.strftime("%Y-%m-%d")
            
            # Yahoo Sports URL pattern
            url = f"{self.BASE_URL}/{sport_path}/scoreboard/?date={date_str}"
            
            client = await self._get_client()
            
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    html = response.text
                    return self._parse_html_scoreboard(html, sport, date)
            except httpx.TimeoutException:
                logger.warning(f"Yahoo timeout for {sport} on {date_str}")
                return []
            except Exception as e:
                logger.error(f"Yahoo fetch error for {sport} on {date_str}: {e}")
                return []
        
        except Exception as e:
            logger.error(f"Yahoo scraper error: {e}")
            return []
    
    def _parse_html_scoreboard(self, html: str, sport: str, date: datetime) -> List[GameUpdate]:
        """Parse Yahoo HTML scoreboard page."""
        games = []
        
        try:
            # Yahoo often embeds JSON data in script tags
            soup = BeautifulSoup(html, "html.parser")
            
            # Try to find embedded JSON data
            script_tags = soup.find_all("script", type="application/json")
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    parsed = self._parse_json_data(data, sport, date)
                    if parsed:
                        games.extend(parsed)
                        break  # Found valid data
                except:
                    continue
            
            # Fallback to HTML parsing if no JSON found
            if not games:
                games = self._parse_html_games(soup, sport, date)
        
        except Exception as e:
            logger.error(f"Error parsing Yahoo HTML: {e}")
        
        return games
    
    def _parse_json_data(self, data: dict, sport: str, date: datetime) -> List[GameUpdate]:
        """Parse embedded JSON data from Yahoo page."""
        games = []
        
        try:
            # Yahoo JSON structure varies - look for common patterns
            events = data.get("games", []) or data.get("events", []) or data.get("scoreboard", {}).get("games", [])
            
            for event in events:
                try:
                    game_update = self._parse_event(event, sport, date)
                    if game_update:
                        games.append(game_update)
                except Exception as e:
                    logger.debug(f"Error parsing Yahoo event: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Yahoo JSON: {e}")
        
        return games
    
    def _parse_html_games(self, soup: BeautifulSoup, sport: str, date: datetime) -> List[GameUpdate]:
        """Parse games from Yahoo HTML structure."""
        games = []
        
        try:
            # Yahoo HTML structure - look for game containers
            # Common classes: game, matchup, scoreboard-game, etc.
            game_containers = soup.find_all(["div", "li"], class_=lambda x: x and ("game" in x.lower() or "matchup" in x.lower()))
            
            for container in game_containers:
                try:
                    game_update = self._parse_html_game(container, sport, date)
                    if game_update:
                        games.append(game_update)
                except Exception as e:
                    logger.debug(f"Error parsing Yahoo HTML game: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Yahoo HTML games: {e}")
        
        return games
    
    def _parse_event(self, event: dict, sport: str, date: datetime) -> Optional[GameUpdate]:
        """Parse a single event from Yahoo JSON."""
        try:
            # Extract teams - Yahoo structure varies
            home_team = event.get("home_team", {}).get("name") or event.get("homeTeam", {}).get("name") or ""
            away_team = event.get("away_team", {}).get("name") or event.get("awayTeam", {}).get("name") or ""
            
            if not home_team or not away_team:
                return None
            
            # Extract scores
            home_score = event.get("home_team", {}).get("score") or event.get("homeScore")
            away_score = event.get("away_team", {}).get("score") or event.get("awayScore")
            
            # Extract status
            raw_status = event.get("status") or event.get("game_status") or "scheduled"
            status = self._normalizer.normalize_status(raw_status, sport)
            
            # Extract period/clock
            period = event.get("period") or event.get("quarter")
            clock = event.get("clock") or event.get("time_remaining")
            
            # Extract start time
            start_time_str = event.get("start_time") or event.get("startTime") or event.get("date")
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(str(start_time_str).replace("Z", "+00:00"))
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
                data_source="yahoo",
            )
        
        except Exception as e:
            logger.debug(f"Error parsing Yahoo event: {e}")
            return None
    
    def _parse_html_game(self, element, sport: str, date: datetime) -> Optional[GameUpdate]:
        """Parse a single game from Yahoo HTML."""
        # This is a placeholder - actual implementation would parse HTML structure
        # Yahoo HTML structure changes frequently, so this needs to be adapted
        logger.debug("Yahoo HTML parsing not fully implemented - JSON preferred")
        return None
