"""Quick test script to fix NFL game times"""

import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

async def test_fix_times():
    """Test the fix-times endpoint"""
    from app.database.session import AsyncSessionLocal
    from app.services.game_time_corrector import GameTimeCorrector
    from app.models.game import Game
    from app.services.sports_config import get_sport_config
    from sqlalchemy import select
    from datetime import datetime, timedelta
    from app.utils.timezone_utils import TimezoneNormalizer
    
    async with AsyncSessionLocal() as db:
        sport_config = get_sport_config("nfl")
        corrector = GameTimeCorrector()
        
        # Find the Eagles @ Chargers game
        result = await db.execute(
            select(Game)
            .where(Game.sport == "NFL")
            .where(Game.home_team.like("%Chargers%"))
            .where(Game.away_team.like("%Eagles%"))
        )
        game = result.scalar_one_or_none()
        
        if not game:
            print("Game not found in database")
            return
        
        print(f"\nFound game: {game.away_team} @ {game.home_team}")
        print(f"Current time: {game.start_time}")
        print(f"Current time (local): {game.start_time.astimezone()}")
        
        # Try to get corrected time
        print("\nFetching corrected time from ESPN...")
        corrected = await corrector.get_corrected_time(
            home_team=game.home_team,
            away_team=game.away_team,
            odds_time=game.start_time,
            sport_code="NFL"
        )
        
        if corrected:
            # Ensure both are timezone-aware
            game_time_utc = TimezoneNormalizer.ensure_utc(game.start_time)
            corrected_utc = TimezoneNormalizer.ensure_utc(corrected)
            diff_hours = abs((game_time_utc - corrected_utc).total_seconds() / 3600.0)
            print(f"Corrected time: {corrected}")
            print(f"Corrected time (local): {corrected.astimezone()}")
            print(f"Difference: {diff_hours:.1f} hours")
            
            if diff_hours >= 6:
                print("\n✓ Time correction needed - updating database...")
                game.start_time = TimezoneNormalizer.ensure_utc(corrected)
                await db.commit()
                print("✓ Database updated!")
            else:
                print(f"\n✗ Difference {diff_hours:.1f}h is less than 6h threshold")
        else:
            print("✗ No corrected time found from ESPN")
            print("\nTrying to fetch ESPN schedule for Dec 8...")
            from datetime import date
            espn_games = await corrector.fetch_espn_schedule_for_date(date(2025, 12, 8), "NFL")
            print(f"Found {len(espn_games)} games on Dec 8:")
            for g in espn_games:
                print(f"  - {g['away_team']} @ {g['home_team']} at {g['start_time']}")

if __name__ == "__main__":
    asyncio.run(test_fix_times())

