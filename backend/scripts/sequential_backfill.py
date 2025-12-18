"""
Sequential backfill runner.

Runs each sport one at a time to avoid SQLite lock contention.
Skips sports/seasons that already meet completion thresholds.
Intended to be run manually or scheduled once every 24 hours.
"""

import asyncio
import sys
from pathlib import Path
from datetime import date
from typing import Dict, Any, List

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.exc import OperationalError

from app.database.session import AsyncSessionLocal
from app.services.ats_ou_calculator import ATSOUCalculator
from app.services.sports_config import SportConfig
from scripts.check_backfill_progress import fetch_progress

# Expected games per season (regular season only)
EXPECTED_GAMES = {
    "NFL": 272,
    "NBA": 1230,
    "NHL": 1312,
    "MLB": 2430,
    "EPL": 380,
    "MLS": 510,
}

# Consider complete if at least this fraction of games are present
COMPLETION_THRESHOLD = 0.8

SPORTS_CONFIG: Dict[str, Dict[str, Any]] = {
    "NFL": {"seasons": ["2024", "2025"], "season_type": "REG", "weeks": None},
    "NBA": {"seasons": ["2024", "2025"], "season_type": "REG", "weeks": None},
    "NHL": {"seasons": ["2024", "2025"], "season_type": "REG", "weeks": None},
    "MLB": {"seasons": ["2024", "2025"], "season_type": "REG", "start_date": None, "end_date": None},
    "EPL": {"seasons": ["2024", "2025"], "season_type": "REG", "start_date": None, "end_date": None},
    "MLS": {"seasons": ["2024", "2025"], "season_type": "REG", "start_date": None, "end_date": None},
}


def needs_processing(progress: Dict[str, Any], sport: str, season: str) -> bool:
    """Determine if a sport/season needs processing based on threshold."""
    sport_progress = progress.get("progress", {}).get(sport, {})
    season_stats = sport_progress.get(season, {})
    games_total = season_stats.get("games_total", 0)
    expected = EXPECTED_GAMES.get(sport, 0)
    if expected == 0:
        return True
    return games_total < expected * COMPLETION_THRESHOLD


async def process_sport(sport: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single sport sequentially for configured seasons."""
    results = {}
    async with AsyncSessionLocal() as db:
        calculator = ATSOUCalculator(db, sport=sport)
        for season in config["seasons"]:
            print(f"\n[SEQ] Processing {sport} {season}...")
            try:
                if sport in ["NFL", "NBA", "NHL"]:
                    res = await calculator.calculate_season_trends(
                        season=season,
                        season_type=config["season_type"],
                        weeks=config.get("weeks"),
                    )
                else:
                    # Date-based sports
                    start_date = config.get("start_date")
                    end_date = config.get("end_date")
                    # Provide default ranges if not set
                    if sport == "MLB":
                        start_date = start_date or date(int(season), 3, 1)
                        end_date = end_date or date(int(season), 11, 1)
                    else:
                        start_date = start_date or date(int(season), 8, 1)
                        end_date = end_date or date(int(season) + 1, 6, 1)
                    res = await calculator.calculate_season_trends(
                        season=season,
                        season_type=config["season_type"],
                        start_date=start_date,
                        end_date=end_date,
                    )
                results[season] = res
                print(f"[SEQ] Done {sport} {season}: {res}")
            except OperationalError as e:
                print(f"[SEQ][ERROR] SQLite lock during {sport} {season}: {e}")
                print("[SEQ] Retrying after 3s...")
                await asyncio.sleep(3)
                try:
                    # Retry once
                    res = await calculator.calculate_season_trends(
                        season=season,
                        season_type=config["season_type"],
                        weeks=config.get("weeks"),
                        start_date=config.get("start_date"),
                        end_date=config.get("end_date"),
                    )
                    results[season] = res
                    print(f"[SEQ] Retry succeeded {sport} {season}: {res}")
                except Exception as retry_err:
                    print(f"[SEQ][FATAL] Retry failed for {sport} {season}: {retry_err}")
                    results[season] = {"error": str(retry_err)}
            except Exception as e:
                print(f"[SEQ][ERROR] Failed {sport} {season}: {e}")
                results[season] = {"error": str(e)}
            # Small pause between seasons to reduce contention
            await asyncio.sleep(1.0)
    return results


async def main():
    print("\n=== SEQUENTIAL BACKFILL ===")
    progress = await fetch_progress()
    print("[SEQ] Current progress snapshot:")
    for sport, seasons in progress["progress"].items():
        for season, stats in seasons.items():
            print(f"  {sport} {season}: {stats['games_total']} games")

    # Process sports sequentially
    summary = {}
    for sport, config in SPORTS_CONFIG.items():
        pending_seasons: List[str] = []
        for season in config["seasons"]:
            if needs_processing(progress, sport, season):
                pending_seasons.append(season)
        if not pending_seasons:
            print(f"[SEQ] Skipping {sport} (already meets threshold)")
            continue

        # Clone config with only pending seasons
        sport_cfg = dict(config)
        sport_cfg["seasons"] = pending_seasons
        print(f"[SEQ] Starting {sport} for seasons {pending_seasons}")
        summary[sport] = await process_sport(sport, sport_cfg)

        # Pause between sports
        await asyncio.sleep(2.0)

    print("\n=== SEQUENTIAL BACKFILL COMPLETE ===")
    print(summary)


if __name__ == "__main__":
    asyncio.run(main())

