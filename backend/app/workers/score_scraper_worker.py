"""Score scraper worker for background score updates."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from app.database.session import AsyncSessionLocal
from app.services.scores.score_scraper_service import ScoreScraperService
from app.services.sports_config import list_supported_sports
from sqlalchemy import select, func
from app.models.game import Game

logger = logging.getLogger(__name__)


class ScoreScraperWorker:
    """Background worker for scraping game scores."""
    
    # Smart cadence: faster when games LIVE, slower otherwise
    LIVE_POLL_INTERVAL = 45  # seconds when games are LIVE
    IDLE_POLL_INTERVAL = 300  # 5 minutes when no games LIVE
    ERROR_BACKOFF_INTERVAL = 60  # seconds after error
    
    def __init__(self):
        self.running = False
        self._task = None
    
    async def start(self):
        """Start the background worker."""
        if self.running:
            logger.warning("ScoreScraperWorker already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("ScoreScraperWorker started")
    
    async def stop(self):
        """Stop the background worker."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ScoreScraperWorker stopped")
    
    async def _run_loop(self):
        """Main polling loop with smart cadence."""
        while self.running:
            try:
                # Check if any games are LIVE
                has_live_games = await self._has_live_games()
                
                # Scrape all supported sports
                await self._scrape_all_sports()
                
                # Wait based on whether games are LIVE
                if has_live_games:
                    await asyncio.sleep(self.LIVE_POLL_INTERVAL)
                else:
                    await asyncio.sleep(self.IDLE_POLL_INTERVAL)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in score scraper loop: {e}")
                await asyncio.sleep(self.ERROR_BACKOFF_INTERVAL)
    
    async def _has_live_games(self) -> bool:
        """Check if any games are currently LIVE."""
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(func.count(Game.id)).where(Game.status == "LIVE")
                )
                count = result.scalar() or 0
                return count > 0
        except Exception as e:
            logger.error(f"Error checking for live games: {e}")
            return False
    
    async def _scrape_all_sports(self):
        """Scrape scores for all supported sports."""
        async with AsyncSessionLocal() as db:
            scraper_service = ScoreScraperService(db)
            
            try:
                for config in list_supported_sports():
                    try:
                        updated = await scraper_service.scrape_and_update_games(
                            sport=config.code,
                            window_days=1,
                        )
                        if updated > 0:
                            logger.info(f"Updated {updated} games for {config.display_name}")
                    except Exception as sport_error:
                        logger.error(f"Error scraping {config.display_name}: {sport_error}")
                        continue
            finally:
                await scraper_service.close()


# Global worker instance
_worker = None


def get_score_scraper_worker() -> ScoreScraperWorker:
    """Get the global ScoreScraperWorker instance."""
    global _worker
    if _worker is None:
        _worker = ScoreScraperWorker()
    return _worker


async def start_score_scraper_worker():
    """Start the score scraper worker."""
    worker = get_score_scraper_worker()
    await worker.start()


async def stop_score_scraper_worker():
    """Stop the score scraper worker."""
    worker = get_score_scraper_worker()
    await worker.stop()
