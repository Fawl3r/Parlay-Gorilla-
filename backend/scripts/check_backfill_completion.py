"""
Check if backfill is complete based on expected games thresholds.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

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

# Sports and seasons to check
SPORTS_CONFIG = {
    "NFL": {"seasons": ["2024", "2025"]},
    "NBA": {"seasons": ["2024", "2025"]},
    "NHL": {"seasons": ["2024", "2025"]},
    "MLB": {"seasons": ["2024", "2025"]},
    "EPL": {"seasons": ["2024", "2025"]},
    "MLS": {"seasons": ["2024", "2025"]},
}


async def check_completion():
    """Check if backfill is complete for all sports/seasons"""
    data = await fetch_progress()
    progress = data["progress"]
    totals = data["totals"]
    
    print("\n" + "="*60)
    print("BACKFILL COMPLETION STATUS")
    print("="*60 + "\n")
    
    all_complete = True
    incomplete_items = []
    
    for sport in sorted(SPORTS_CONFIG.keys()):
        sport_config = SPORTS_CONFIG[sport]
        expected = EXPECTED_GAMES.get(sport, 0)
        threshold = int(expected * COMPLETION_THRESHOLD)
        
        print(f"{sport} (Expected: {expected} games, Threshold: {threshold}):")
        
        for season in sport_config["seasons"]:
            season_stats = progress.get(sport, {}).get(season, {})
            games_total = season_stats.get("games_total", 0)
            games_with_ats = season_stats.get("games_with_ats", 0)
            games_with_ou = season_stats.get("games_with_ou", 0)
            
            is_complete = games_total >= threshold if expected > 0 else games_total > 0
            status = "✓ COMPLETE" if is_complete else "✗ INCOMPLETE"
            
            if not is_complete:
                all_complete = False
                incomplete_items.append(f"{sport} {season}")
            
            ats_pct = f"{(games_with_ats / games_total * 100):.1f}%" if games_total else "0%"
            ou_pct = f"{(games_with_ou / games_total * 100):.1f}%" if games_total else "0%"
            
            print(f"  {season}: {games_total}/{expected} games {status}")
            print(f"    ATS: {games_with_ats} ({ats_pct}), O/U: {games_with_ou} ({ou_pct})")
        
        print()
    
    print("="*60)
    print(f"Total Games: {totals['games_total']}")
    print(f"Total with ATS: {totals['games_with_ats']}")
    print(f"Total with O/U: {totals['games_with_ou']}")
    print("="*60)
    
    if all_complete:
        print("\n✅ BACKFILL IS COMPLETE")
        print("All sports/seasons meet the 80% completion threshold.")
    else:
        print("\n⚠️  BACKFILL IS INCOMPLETE")
        print(f"Missing data for: {', '.join(incomplete_items)}")
        print("\nTo complete backfill, run:")
        print("  python scripts/sequential_backfill.py")
        print("  OR")
        print("  curl -X POST http://localhost:8000/api/games/backfill-all-sports")
    
    print()
    
    return all_complete


if __name__ == "__main__":
    asyncio.run(check_completion())

