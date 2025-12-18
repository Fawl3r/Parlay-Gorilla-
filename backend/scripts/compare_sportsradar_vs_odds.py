"""
Compare SportsRadar schedule vs The Odds API games for NFL to spot time mismatches.
Falls back to ESPN if SportsRadar fails.

Usage:
    cd backend
    python -m scripts.compare_sportsradar_vs_odds
"""

import asyncio
import httpx
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from app.database.session import AsyncSessionLocal
from app.services.odds_fetcher import OddsFetcherService
from app.services.data_fetchers.sportsradar_nfl import SportsRadarNFL
from app.services.data_fetchers.espn_scraper import ESPNScraper
from app.utils.timezone_utils import TimezoneNormalizer


def _normalize_team_name(name: str) -> str:
    """Normalize team name for matching (lowercase, remove spaces/punctuation)."""
    return "".join(ch for ch in name.lower() if ch.isalnum())


def _make_match_key(away: str, home: str) -> str:
    return f"{_normalize_team_name(away)}@{_normalize_team_name(home)}"


def _parse_sr_time(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return TimezoneNormalizer.ensure_utc(dt)
    except Exception:
        return None


async def fetch_odds_games() -> List[Dict]:
    async with AsyncSessionLocal() as db:
        fetcher = OddsFetcherService(db)
        games = await fetcher.get_or_fetch_games("nfl", force_refresh=False)
        normalized = []
        for g in games:
            normalized.append(
                {
                    "home": g.home_team,
                    "away": g.away_team,
                    "start": TimezoneNormalizer.ensure_utc(g.start_time),
                    "status": g.status,
                }
            )
        return normalized


async def fetch_sportsradar_schedule(days: int = 2) -> Tuple[List[Dict], Optional[str]]:
    """Fetch SportsRadar schedule. Returns (games, error_message)."""
    client = SportsRadarNFL()
    today = date.today()
    all_games: List[Dict] = []
    errors = []
    
    # Test one request to see actual error
    test_date = today
    endpoint = f"games/{test_date.year}/{test_date.month}/{test_date.day}/schedule.json"
    url = f"{client.base_url}/{endpoint}"
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            response = await http_client.get(
                url,
                params={"api_key": client.api_key}
            )
            if response.status_code == 403:
                error_msg = f"SportsRadar 403 Forbidden - API key invalid or quota exceeded"
                try:
                    error_body = response.json()
                    error_msg += f": {error_body}"
                except:
                    error_msg += f": {response.text[:200]}"
                return [], error_msg
            elif response.status_code != 200:
                error_msg = f"SportsRadar {response.status_code}: {response.text[:200]}"
                return [], error_msg
    except Exception as e:
        error_msg = f"SportsRadar request error: {e}"
        return [], error_msg
    
    # If test passed, fetch all days
    for offset in range(days):
        target = today + timedelta(days=offset)
        schedule = await client.get_schedule(start_date=target, end_date=target)
        for game in schedule:
            all_games.append(
                {
                    "home": game.get("home_team"),
                    "away": game.get("away_team"),
                    "start": _parse_sr_time(game.get("scheduled")),
                    "status": game.get("status"),
                }
            )
    return all_games, None


async def fetch_espn_schedule(days: int = 3) -> List[Dict]:
    """Fetch NFL schedule from ESPN scoreboard API."""
    base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    all_games: List[Dict] = []
    today = date.today()
    
    for offset in range(days):
        target = today + timedelta(days=offset)
        date_str = target.strftime("%Y%m%d")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(base_url, params={"dates": date_str})
                if response.status_code == 200:
                    data = response.json()
                    events = data.get("events", [])
                    
                    for event in events:
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
                            except:
                                pass
                        
                        all_games.append({
                            "home": home_team,
                            "away": away_team,
                            "start": start_time,
                            "status": comp.get("status", {}).get("type", {}).get("name", "scheduled"),
                        })
        except Exception as e:
            print(f"[ESPN] Error fetching {date_str}: {e}")
            continue
    
    return all_games


def compare_games(odds_games: List[Dict], sr_games: List[Dict]) -> None:
    sr_index = {
        _make_match_key(g["away"], g["home"]): g for g in sr_games if g["home"] and g["away"]
    }

    mismatches = []
    missing_in_sr = []

    for og in odds_games:
        key = _make_match_key(og["away"], og["home"])
        sr = sr_index.get(key)
        if not sr:
            missing_in_sr.append(og)
            continue

        og_start = og["start"]
        sr_start = sr["start"]
        if not og_start or not sr_start:
            mismatches.append((og, sr, "missing time"))
            continue

        diff_hours = abs((og_start - sr_start).total_seconds()) / 3600.0
        if diff_hours > 0.5:  # more than 30 minutes difference
            mismatches.append((og, sr, f"time diff {diff_hours:.2f}h"))

    print("\n=== Comparison Report ===")
    print(f"Odds API games: {len(odds_games)} | SportsRadar games: {len(sr_games)}")
    print(f"Missing in SportsRadar: {len(missing_in_sr)} | Time mismatches: {len(mismatches)}")

    if missing_in_sr:
        print("\nMissing in SportsRadar schedule:")
        for g in missing_in_sr:
            print(
                f"  {g['away']} @ {g['home']} | odds start: {g['start']} | status: {g['status']}"
            )

    if mismatches:
        print("\nStart time mismatches (>30m):")
        for og, sr, reason in mismatches:
            print(
                f"  {og['away']} @ {og['home']} | odds: {og['start']} | sr: {sr['start']} | {reason}"
            )

    if not missing_in_sr and not mismatches:
        print("\nAll matched within 30 minutes.")


async def main():
    load_dotenv()
    print("Fetching games from The Odds API...")
    odds_games = await fetch_odds_games()
    print(f"Found {len(odds_games)} games from Odds API\n")
    
    # Try SportsRadar first
    print("Trying SportsRadar...")
    sr_games, sr_error = await fetch_sportsradar_schedule(days=3)
    
    if sr_error:
        print(f"SportsRadar failed: {sr_error}\n")
        print("Falling back to ESPN...")
        sr_games = await fetch_espn_schedule(days=3)
        print(f"Found {len(sr_games)} games from ESPN\n")
    else:
        print(f"Found {len(sr_games)} games from SportsRadar\n")
    
    compare_games(odds_games, sr_games)


if __name__ == "__main__":
    asyncio.run(main())

