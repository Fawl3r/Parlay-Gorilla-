"""Test the full scraper flow: stats fetch, ATS/O/U calculation, injuries"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.session import AsyncSessionLocal
from app.workers.scraper_worker import ScraperWorker


async def test_full_scraper_flow():
    """Test the complete scraper worker flow"""
    print("\n" + "="*60)
    print("TEST: Full Scraper Worker Flow")
    print("="*60 + "\n")
    
    worker = ScraperWorker()
    
    # Test with NFL only for faster testing
    print("Running scraper for NFL...")
    print("-" * 40)
    
    await worker.run_full_scrape(sport="nfl")
    
    print("\n" + "="*60)
    print("Scraper run complete!")
    print("="*60 + "\n")
    
    # Verify results
    async with AsyncSessionLocal() as db:
        from app.models.team_stats import TeamStats
        from sqlalchemy import select, and_, func
        
        # Count teams with stats
        result = await db.execute(
            select(func.count(TeamStats.id))
            .where(
                and_(
                    TeamStats.season == "2024",
                    TeamStats.week.is_(None),
                    TeamStats.points_per_game > 0
                )
            )
        )
        teams_with_stats = result.scalar() or 0
        
        print(f"Teams with offensive stats: {teams_with_stats}")
        
        # Count teams with ATS data
        result = await db.execute(
            select(func.count(TeamStats.id))
            .where(
                and_(
                    TeamStats.season == "2024",
                    TeamStats.week.is_(None),
                    TeamStats.ats_wins > 0
                )
            )
        )
        teams_with_ats = result.scalar() or 0
        
        print(f"Teams with ATS data: {teams_with_ats}")
        
        # Check for percentage issues
        result = await db.execute(
            select(TeamStats)
            .where(
                and_(
                    TeamStats.season == "2024",
                    TeamStats.week.is_(None),
                    TeamStats.ats_win_percentage > 100.0
                )
            )
            .limit(5)
        )
        bad_percentages = result.scalars().all()
        
        if bad_percentages:
            print(f"\n⚠ WARNING: Found {len(bad_percentages)} teams with percentages > 100%")
            for stats in bad_percentages:
                print(f"  {stats.team_name}: {stats.ats_win_percentage:.2f}%")
        else:
            print(f"\n✓ No percentage issues found (all percentages <= 100%)")


if __name__ == "__main__":
    asyncio.run(test_full_scraper_flow())



