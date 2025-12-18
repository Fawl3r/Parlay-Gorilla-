"""Service to correct game start times using ESPN as source of truth."""

import httpx
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List
import logging

from app.utils.timezone_utils import TimezoneNormalizer

logger = logging.getLogger(__name__)


class GameTimeCorrector:
    """Corrects game start times by cross-referencing with ESPN schedule."""
    
    ESPN_BASE_URLS = {
        "NFL": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
        "NBA": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
        "NHL": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
        "MLB": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
        # College
        "NCAAF": "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard",
        "NCAAB": "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard",
        "MLS": "https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/scoreboard",
        "EPL": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
        "LALIGA": "https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard",
        "UCL": "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard",
        "SOCCER": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",  # Default to EPL
    }
    TIMEOUT = 10.0
    
    # Team name normalization for matching (common across sports)
    TEAM_NORMALIZE_MAP = {
        # NFL
        "los angeles chargers": "chargers",
        "los angeles rams": "rams",
        "kansas city": "chiefs",
        "new england": "patriots",
        "new york giants": "giants",
        "new york jets": "jets",
        "tampa bay": "buccaneers",
        "green bay": "packers",
        "san francisco": "49ers",
        "las vegas": "raiders",
        # NBA
        "los angeles lakers": "lakers",
        "los angeles clippers": "clippers",
        "golden state": "warriors",
        "new york": "knicks",
        "new orleans": "pelicans",
        # NHL
        "new york rangers": "rangers",
        "new york islanders": "islanders",
        "tampa bay": "lightning",
        "san jose": "sharks",
    }
    
    def _normalize_team_name(self, name: str) -> str:
        """Normalize team name for matching."""
        normalized = name.lower().strip()
        # Remove city prefixes for matching
        for full_name, short_name in self.TEAM_NORMALIZE_MAP.items():
            if full_name in normalized:
                normalized = normalized.replace(full_name, short_name)
        # Remove common city prefixes (US sports)
        city_prefixes = [
            "los angeles ", "new york ", "san francisco ", "tampa bay ",
            "green bay ", "kansas city ", "las vegas ", "new england ",
            "new orleans ", "golden state ", "san jose ", "st. louis ",
            "st louis ", "minnesota ", "washington ", "boston ",
            "charlotte ", "philadelphia ", "phoenix ", "portland ",
            "oklahoma city ", "utah ", "indiana ", "brooklyn ",
        ]
        for prefix in city_prefixes:
            normalized = normalized.replace(prefix, "")
        
        # Remove common soccer prefixes/suffixes
        soccer_terms = [
            "fc ", " cf ", " united ", " city ", " town ", " athletic ",
            " wanderers ", " rovers ", " albion ", " hotspur ", " spurs ",
        ]
        for term in soccer_terms:
            normalized = normalized.replace(term, " ")
        
        # Clean up extra spaces
        normalized = " ".join(normalized.split())
        # Extract last word (team name)
        parts = normalized.split()
        return parts[-1] if parts else normalized
    
    def _teams_match(self, team1: str, team2: str) -> bool:
        """Check if two team names refer to the same team."""
        norm1 = self._normalize_team_name(team1)
        norm2 = self._normalize_team_name(team2)
        
        # Direct match
        if norm1 == norm2:
            return True
        
        # Check if one contains the other (handles "eagles" vs "philadelphia eagles")
        if norm1 in norm2 or norm2 in norm1:
            return True
        
        # Also check original names (in case normalization loses important info)
        orig1_lower = team1.lower()
        orig2_lower = team2.lower()
        if norm1 in orig2_lower or norm2 in orig1_lower:
            return True
        if orig1_lower in orig2_lower or orig2_lower in orig1_lower:
            return True
        
        # Check common team name variations
        team_variations = {
            "chargers": ["charger"],
            "chiefs": ["chief"],
            "eagles": ["eagle"],
            "texans": ["texan"],
            "patriots": ["patriot"],
            "giants": ["giant"],
            "jets": ["jet"],
            "bills": ["bill"],
            "ravens": ["raven"],
            "steelers": ["steeler"],
            "browns": ["brown"],
            "bengals": ["bengal"],
            "titans": ["titan"],
            "colts": ["colt"],
            "jaguars": ["jaguar"],
            "raiders": ["raider"],
            "broncos": ["bronco"],
            "cowboys": ["cowboy"],
            "commanders": ["commander", "redskins"],
            "bears": ["bear"],
            "lions": ["lion"],
            "packers": ["packer"],
            "vikings": ["viking"],
            "falcons": ["falcon"],
            "panthers": ["panther"],
            "saints": ["saint"],
            "buccaneers": ["buccaneer", "bucs"],
            "cardinals": ["cardinal"],
            "rams": ["ram"],
            "49ers": ["49er", "niners"],
            "seahawks": ["seahawk"],
            "dolphins": ["dolphin"],
        }
        
        for base_name, variants in team_variations.items():
            if norm1 == base_name or norm1 in variants:
                if norm2 == base_name or norm2 in variants:
                    return True
        
        return False
    
    async def fetch_espn_schedule_for_date(
        self, 
        target_date: date,
        sport_code: str = "NFL"
    ) -> List[Dict]:
        """Fetch schedule from ESPN for a specific date and sport."""
        date_str = target_date.strftime("%Y%m%d")
        base_url = self.ESPN_BASE_URLS.get(sport_code)
        
        if not base_url:
            logger.warning(f"[TIME_CORRECTOR] No ESPN URL for sport {sport_code}")
            return []
        
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(
                    base_url,
                    params={"dates": date_str}
                )
                if response.status_code != 200:
                    logger.warning(f"[TIME_CORRECTOR] ESPN returned {response.status_code} for {sport_code} on {date_str}")
                    return []
                
                data = response.json()
                events = data.get("events", [])
                games = []
                
                for event in events:
                    event_id = str(event.get("id") or "").strip()
                    competitions = event.get("competitions", [])
                    if not competitions:
                        continue
                    
                    comp = competitions[0]
                    competitors = comp.get("competitors", [])
                    if len(competitors) < 2:
                        continue
                    
                    # Find home and away
                    home_comp = next((c for c in competitors if c.get("homeAway") == "home"), None)
                    away_comp = next((c for c in competitors if c.get("homeAway") == "away"), None)
                    
                    if not home_comp or not away_comp:
                        continue
                    
                    home_team = home_comp.get("team", {}).get("displayName", "")
                    away_team = away_comp.get("team", {}).get("displayName", "")
                    
                    # Parse start time
                    date_str_raw = comp.get("date", "")
                    start_time = None
                    if date_str_raw:
                        try:
                            dt = datetime.fromisoformat(date_str_raw.replace("Z", "+00:00"))
                            start_time = TimezoneNormalizer.ensure_utc(dt)
                        except Exception as e:
                            logger.debug(f"[TIME_CORRECTOR] Failed to parse time {date_str_raw}: {e}")
                            continue
                    
                    games.append({
                        "event_id": event_id,
                        "home_team": home_team,
                        "away_team": away_team,
                        "start_time": start_time,
                        "status": comp.get("status", {}).get("type", {}).get("name", "scheduled"),
                    })
                
                return games
        except httpx.TimeoutException:
            logger.warning(f"[TIME_CORRECTOR] ESPN timeout for {date_str}")
            return []
        except Exception as e:
            logger.error(f"[TIME_CORRECTOR] ESPN error for {date_str}: {e}")
            return []
    
    async def get_corrected_time(
        self,
        home_team: str,
        away_team: str,
        odds_time: datetime,
        sport_code: str = "NFL",
        search_days: int = 3
    ) -> Optional[datetime]:
        """
        Get corrected start time from ESPN for a game.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            odds_time: Time from The Odds API (may be incorrect)
            sport_code: Sport code (NFL, NBA, NHL, MLB)
            search_days: Number of days around odds_time to search
        
        Returns:
            Corrected datetime or None if not found
        """
        # Ensure odds_time is timezone-aware
        odds_time = TimezoneNormalizer.ensure_utc(odds_time)
        
        # Search around the odds time (before and after)
        search_date = odds_time.date()
        
        for offset in range(-search_days, search_days + 1):
            target_date = search_date + timedelta(days=offset)
            espn_games = await self.fetch_espn_schedule_for_date(target_date, sport_code)
            
            for game in espn_games:
                home_match = self._teams_match(game["home_team"], home_team)
                away_match = self._teams_match(game["away_team"], away_team)
                
                if home_match and away_match:
                    corrected = game["start_time"]
                    if corrected:
                        time_diff = abs((odds_time - corrected).total_seconds() / 3600.0)
                        logger.info(
                            f"[TIME_CORRECTOR] Found match: {away_team} @ {home_team} | "
                            f"Odds: {odds_time} | ESPN: {corrected} | Diff: {time_diff:.1f}h"
                        )
                        # Return corrected time if difference is significant (>= 6 hours)
                        if time_diff >= 6:
                            logger.info(
                                f"[TIME_CORRECTOR] Significant time mismatch detected: "
                                f"{time_diff:.1f}h difference - will correct"
                            )
                            return corrected
                        else:
                            logger.debug(
                                f"[TIME_CORRECTOR] Time difference {time_diff:.1f}h is within tolerance, not correcting"
                            )
                            return None  # Don't correct small differences
                elif home_match or away_match:
                    # Partial match - log for debugging
                    logger.debug(
                        f"[TIME_CORRECTOR] Partial match: ESPN {game['away_team']} @ {game['home_team']} "
                        f"vs Odds {away_team} @ {home_team} (home_match={home_match}, away_match={away_match})"
                    )
        
        logger.debug(
            f"[TIME_CORRECTOR] No match found for {away_team} @ {home_team} "
            f"({sport_code}) around {search_date} (±{search_days} days)"
        )
        return None
    
    async def correct_game_time(
        self,
        home_team: str,
        away_team: str,
        odds_time: datetime,
        sport_code: str = "NFL"
    ) -> datetime:
        """
        Get corrected time, falling back to odds_time if ESPN doesn't have it.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            odds_time: Time from The Odds API
            sport_code: Sport code (NFL, NBA, NHL, MLB)
        
        Returns the corrected time or the original odds_time if no correction found.
        """
        corrected = await self.get_corrected_time(home_team, away_team, odds_time, sport_code)
        return corrected if corrected else odds_time

