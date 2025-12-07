"""Scraper worker for fetching stats from ESPN, Covers, Rotowire"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.services.stats_scraper import StatsScraperService
from app.models.team_stats import TeamStats
from app.services.sports_config import get_sport_config


class ScraperWorker:
    """Background worker for scraping team stats and data"""
    
    def __init__(self):
        self.scraper = StatsScraperService()
    
    async def run_full_scrape(self, sport: str = None):
        """
        Run full scrape for a sport or all sports
        
        Args:
            sport: Sport to scrape (nfl, nba, mlb, nhl) or None for all
        """
        sports = [sport] if sport else ["nfl", "nba", "mlb", "nhl"]
        
        async with AsyncSessionLocal() as db:
            for sport_key in sports:
                try:
                    print(f"[SCRAPER_WORKER] Starting scrape for {sport_key.upper()}...")
                    
                    # Fetch team stats
                    stats_data = await self.scraper.fetch_team_stats(sport_key)
                    
                    if stats_data:
                        # Store in database
                        await self._store_team_stats(db, sport_key, stats_data)
                        await db.commit()
                        print(f"[SCRAPER_WORKER] Stored {len(stats_data)} team stats for {sport_key.upper()}")
                    else:
                        print(f"[SCRAPER_WORKER] No stats data for {sport_key.upper()}")
                        
                except Exception as e:
                    print(f"[SCRAPER_WORKER] Error scraping {sport_key}: {e}")
                    await db.rollback()
                    continue
    
    async def _store_team_stats(
        self, 
        db: AsyncSession, 
        sport: str, 
        stats_data: List[Dict[str, Any]]
    ):
        """Store team stats in database"""
        from sqlalchemy import select
        
        for stat in stats_data:
            # Check if stats already exist
            result = await db.execute(
                select(TeamStats).where(
                    TeamStats.team_name == stat.get("team_name"),
                    TeamStats.season == stat.get("season", "2024"),
                    TeamStats.week == stat.get("week"),
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing
                for key, value in stat.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                # Create new
                team_stat = TeamStats(**stat)
                db.add(team_stat)
    
    async def run_injury_scrape(self, sport: str = None):
        """Scrape injury data for teams"""
        sports = [sport] if sport else ["nfl", "nba", "mlb", "nhl"]
        
        for sport_key in sports:
            try:
                print(f"[SCRAPER_WORKER] Fetching injuries for {sport_key.upper()}...")
                injuries = await self.scraper.fetch_injuries(sport_key)
                
                if injuries:
                    print(f"[SCRAPER_WORKER] Found {len(injuries)} injury reports for {sport_key.upper()}")
                    # Store injuries (would need an Injury model)
                    # For now, just log
            except Exception as e:
                print(f"[SCRAPER_WORKER] Error fetching injuries for {sport_key}: {e}")


async def run_scraper_worker():
    """Main entry point for scraper worker"""
    worker = ScraperWorker()
    await worker.run_full_scrape()


if __name__ == "__main__":
    asyncio.run(run_scraper_worker())

