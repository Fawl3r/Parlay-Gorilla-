"""Heartbeat worker for system status tracking."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from app.database.session import AsyncSessionLocal
from app.models.system_heartbeat import SystemHeartbeat
from sqlalchemy import select, func
from app.models.parlay_feed_event import ParlayFeedEvent

logger = logging.getLogger(__name__)


class HeartbeatWorker:
    """Background worker for updating system heartbeats."""
    
    POLL_INTERVAL = 30  # seconds
    
    def __init__(self):
        self.running = False
        self._task = None
    
    async def start(self):
        """Start the background worker."""
        if self.running:
            logger.warning("HeartbeatWorker already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("HeartbeatWorker started")
    
    async def stop(self):
        """Stop the background worker."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("HeartbeatWorker stopped")
    
    async def _run_loop(self):
        """Main heartbeat loop."""
        while self.running:
            try:
                await self._update_heartbeats()
                await asyncio.sleep(self.POLL_INTERVAL)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(self.POLL_INTERVAL)
    
    async def _update_heartbeats(self):
        """Update all system heartbeats with current stats."""
        async with AsyncSessionLocal() as db:
            try:
                # Update heartbeat worker's own heartbeat
                result = await db.execute(
                    select(SystemHeartbeat).where(SystemHeartbeat.name == "heartbeat_worker")
                )
                heartbeat = result.scalar_one_or_none()
                
                # Get stats from other workers
                scraper_result = await db.execute(
                    select(SystemHeartbeat).where(SystemHeartbeat.name == "scraper_worker")
                )
                scraper_heartbeat = scraper_result.scalar_one_or_none()
                
                settlement_result = await db.execute(
                    select(SystemHeartbeat).where(SystemHeartbeat.name == "settlement_worker")
                )
                settlement_heartbeat = settlement_result.scalar_one_or_none()
                
                # Count parlays settled today
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                result = await db.execute(
                    select(func.count(ParlayFeedEvent.id)).where(
                        and_(
                            ParlayFeedEvent.event_type.in_(["PARLAY_WON", "PARLAY_LOST"]),
                            ParlayFeedEvent.created_at >= today_start,
                        )
                    )
                )
                parlays_settled_today = result.scalar() or 0
                
                if heartbeat:
                    heartbeat.last_beat_at = datetime.utcnow()
                    heartbeat.meta = {
                        "scraper_last_beat": scraper_heartbeat.last_beat_at.isoformat() if scraper_heartbeat else None,
                        "settlement_last_beat": settlement_heartbeat.last_beat_at.isoformat() if settlement_heartbeat else None,
                        "parlays_settled_today": parlays_settled_today,
                    }
                else:
                    heartbeat = SystemHeartbeat(
                        name="heartbeat_worker",
                        last_beat_at=datetime.utcnow(),
                        meta={
                            "scraper_last_beat": scraper_heartbeat.last_beat_at.isoformat() if scraper_heartbeat else None,
                            "settlement_last_beat": settlement_heartbeat.last_beat_at.isoformat() if settlement_heartbeat else None,
                            "parlays_settled_today": parlays_settled_today,
                        },
                    )
                    db.add(heartbeat)
                
                await db.commit()
            
            except Exception as e:
                logger.error(f"Error updating heartbeats: {e}")
                await db.rollback()


# Global worker instance
_worker = None


def get_heartbeat_worker() -> HeartbeatWorker:
    """Get the global HeartbeatWorker instance."""
    global _worker
    if _worker is None:
        _worker = HeartbeatWorker()
    return _worker


async def start_heartbeat_worker():
    """Start the heartbeat worker."""
    worker = get_heartbeat_worker()
    await worker.start()


async def stop_heartbeat_worker():
    """Stop the heartbeat worker."""
    worker = get_heartbeat_worker()
    await worker.stop()
