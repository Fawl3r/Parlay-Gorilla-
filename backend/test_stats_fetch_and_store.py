"""Test script to verify team stats are being fetched and stored correctly"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.session import AsyncSessionLocal
from app.services.stats_scraper import StatsScraperService
from app.models.team_stats import TeamStats
from sqlalchemy import select, and_


async def test_fetch_and_store_stats():
    """Test fetching and storing team stats"""
    print("\n" + "="*60)
    print("TEST: Fetch and Store Team Stats")
    print("="*60 + "\n")
    
    async with AsyncSessionLocal() as db:
        scraper = StatsScraperService(db)
        
        # Test teams
        test_teams = [
            ("Miami Dolphins", "NFL"),
            ("Cincinnati Bengals", "NFL"),
            ("Washington Commanders", "NFL"),
            ("Philadelphia Eagles", "NFL"),
        ]
        
        season = "2024"
        
        for team_name, league in test_teams:
            print(f"\nTesting: {team_name} ({league})")
            print("-" * 40)
            
            # Fetch and store stats
            stats = await scraper.fetch_and_store_team_stats(
                team_name=team_name,
                league=league,
                season=season
            )
            
            if stats:
                print(f"✓ Stats fetched successfully")
                print(f"  Record: {stats.get('record', {}).get('wins', 0)}-{stats.get('record', {}).get('losses', 0)}")
                print(f"  PPG: {stats.get('offense', {}).get('points_per_game', 0):.1f}")
                print(f"  YPG: {stats.get('offense', {}).get('yards_per_game', 0):.1f}")
                print(f"  PAPG: {stats.get('defense', {}).get('points_allowed_per_game', 0):.1f}")
            else:
                print(f"✗ Failed to fetch stats")
                continue
            
            # Verify stats are in database
            result = await db.execute(
                select(TeamStats).where(
                    and_(
                        TeamStats.team_name == team_name,
                        TeamStats.season == season,
                        TeamStats.week.is_(None)
                    )
                )
            )
            db_stats = result.scalar_one_or_none()
            
            if db_stats:
                print(f"✓ Stats stored in database")
                print(f"  DB Record: {db_stats.wins}-{db_stats.losses}")
                print(f"  DB PPG: {db_stats.points_per_game:.1f}")
                print(f"  DB YPG: {db_stats.yards_per_game:.1f}")
                print(f"  DB PAPG: {db_stats.points_allowed_per_game:.1f}")
                
                # Check if stats are non-zero (indicating real data)
                if db_stats.points_per_game > 0:
                    print(f"  ✓ Has offensive stats")
                else:
                    print(f"  ⚠ Offensive stats are zero")
                    
                if db_stats.points_allowed_per_game > 0:
                    print(f"  ✓ Has defensive stats")
                else:
                    print(f"  ⚠ Defensive stats are zero")
            else:
                print(f"✗ Stats NOT found in database")
        
        await db.commit()
        print("\n" + "="*60)
        print("Test complete!")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_fetch_and_store_stats())



