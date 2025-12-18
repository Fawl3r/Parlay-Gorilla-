"""Check if 2025 NFL data is available from SportsRadar"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.data_fetchers import get_nfl_fetcher


async def check_2025_data():
    """Check what 2025 data is available"""
    print("\n" + "="*60)
    print("CHECKING 2025 NFL DATA AVAILABILITY")
    print("="*60 + "\n")
    
    fetcher = get_nfl_fetcher()
    
    # Check 2025 season schedule
    print("Checking 2025 REG season schedule...")
    try:
        data = await fetcher._make_request("games/2025/REG/schedule.json")
        if data:
            weeks = data.get('weeks', [])
            print(f"[OK] Found {len(weeks)} weeks in 2025 REG season")
            
            # Count completed games
            completed_count = 0
            total_games = 0
            for week in weeks:
                week_num = week.get('sequence', week.get('number', 0))
                games = week.get('games', [])
                total_games += len(games)
                for game in games:
                    if game.get('status') == 'closed':
                        completed_count += 1
            
            print(f"  Total games: {total_games}")
            print(f"  Completed games: {completed_count}")
            print(f"  Scheduled games: {total_games - completed_count}")
            
            # Show recent weeks
            if weeks:
                print(f"\n  Recent weeks:")
                for week in weeks[-5:]:  # Last 5 weeks
                    week_num = week.get('sequence', week.get('number', 0))
                    games = week.get('games', [])
                    completed = sum(1 for g in games if g.get('status') == 'closed')
                    print(f"    Week {week_num}: {completed}/{len(games)} completed")
        else:
            print("[ERROR] No data returned for 2025 REG season")
    except Exception as e:
        print(f"[ERROR] Error checking 2025 data: {e}")
        import traceback
        traceback.print_exc()
    
    # Also check current date
    print(f"\nCurrent date: {datetime.now().strftime('%Y-%m-%d')}")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(check_2025_data())

