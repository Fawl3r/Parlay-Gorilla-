"""
Backfill script to populate 2024 and 2025 data for all sports.

This script ensures all sports have historical data stored so we don't
need to re-fetch it from external APIs.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import AsyncSessionLocal
from app.services.ats_ou_calculator import ATSOUCalculator


SPORTS_CONFIG = {
    "NFL": {
        "seasons": ["2024", "2025"],
        "season_type": "REG",
        "weeks": None,  # All weeks
    },
    "NBA": {
        "seasons": ["2024", "2025"],
        "season_type": "REG",
        "weeks": None,  # All weeks
    },
    "NHL": {
        "seasons": ["2024", "2025"],
        "season_type": "REG",
        "weeks": None,  # All weeks
    },
    "MLB": {
        "seasons": ["2024", "2025"],
        "season_type": "REG",
        "start_date": None,  # Will use defaults
        "end_date": None,  # Will use defaults
    },
    "EPL": {
        "seasons": ["2024", "2025"],
        "season_type": "REG",
        "start_date": None,  # Will use defaults
        "end_date": None,  # Will use defaults
    },
    "MLS": {
        "seasons": ["2024", "2025"],
        "season_type": "REG",
        "start_date": None,  # Will use defaults
        "end_date": None,  # Will use defaults
    },
}


async def backfill_sport(sport: str, config: dict, db):
    """Backfill data for a single sport"""
    print(f"\n{'='*60}")
    print(f"BACKFILLING {sport}")
    print(f"{'='*60}\n")
    
    calculator = ATSOUCalculator(db, sport=sport)
    total_games = 0
    total_teams = set()
    
    for season in config["seasons"]:
        print(f"  Processing {sport} {season}...")
        
        try:
            if sport in ["NFL", "NBA", "NHL"]:
                result = await calculator.calculate_season_trends(
                    season=season,
                    season_type=config["season_type"],
                    weeks=config["weeks"]
                )
            elif sport in ["MLB", "EPL", "MLS"]:
                result = await calculator.calculate_season_trends(
                    season=season,
                    season_type=config["season_type"],
                    start_date=config.get("start_date"),
                    end_date=config.get("end_date")
                )
            else:
                print(f"    [SKIP] Unsupported sport: {sport}")
                continue
            
            games_processed = result.get("games_processed", 0)
            teams_updated = result.get("teams_updated", 0)
            teams = result.get("teams", [])
            
            total_games += games_processed
            total_teams.update(teams)
            
            print(f"    ✓ {season}: {games_processed} games, {teams_updated} teams")
            
            if result.get("error"):
                print(f"    ⚠ Error: {result['error']}")
        
        except Exception as e:
            print(f"    ✗ Error processing {sport} {season}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n  {sport} Summary: {total_games} total games, {len(total_teams)} teams")
    return total_games, len(total_teams)


async def main():
    """Backfill all sports"""
    print("\n" + "="*60)
    print("BACKFILLING ALL SPORTS DATA (2024 & 2025)")
    print("="*60)
    print("\nThis will populate game results and team stats for all sports.")
    print("Existing data will be skipped to avoid duplicate API calls.\n")
    
    async with AsyncSessionLocal() as db:
        total_games_all = 0
        total_teams_all = set()
        
        for sport, config in SPORTS_CONFIG.items():
            try:
                games, teams = await backfill_sport(sport, config, db)
                total_games_all += games
                total_teams_all.update([f"{sport}:{t}" for t in range(teams)])
            except Exception as e:
                print(f"\n✗ Failed to backfill {sport}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("\n" + "="*60)
        print("BACKFILL COMPLETE")
        print("="*60)
        print(f"\nTotal games processed: {total_games_all}")
        print(f"Total teams updated: {len(total_teams_all)}")
        print(f"\nAll sports now have 2024 and 2025 data stored.")
        print("Future fetches will only get new/updated data.\n")


if __name__ == "__main__":
    asyncio.run(main())

