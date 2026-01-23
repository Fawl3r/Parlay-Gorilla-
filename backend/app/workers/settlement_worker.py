"""Settlement worker for processing parlay settlements."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from app.database.session import AsyncSessionLocal
from app.services.settlement.settlement_service import SettlementService
from sqlalchemy import select, and_
from app.models.game import Game

logger = logging.getLogger(__name__)


class SettlementWorker:
    """Background worker for settling parlays."""
    
    # Smart cadence: faster during active games, slower otherwise
    ACTIVE_POLL_INTERVAL = 90  # 1.5 minutes during active games
    IDLE_POLL_INTERVAL = 300  # 5 minutes when no active games
    ERROR_BACKOFF_INTERVAL = 60  # seconds after error
    
    def __init__(self):
        self.running = False
        self._task = None
    
    async def start(self):
        """Start the background worker."""
        if self.running:
            logger.warning("SettlementWorker already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("SettlementWorker started")
    
    async def stop(self):
        """Stop the background worker."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("SettlementWorker stopped")
    
    async def _run_loop(self):
        """Main polling loop with smart cadence."""
        while self.running:
            try:
                # Check if any games are LIVE or recently FINAL
                has_active_games = await self._has_active_games()
                
                # Process settlements
                await self._process_settlements()
                
                # Wait based on activity
                if has_active_games:
                    await asyncio.sleep(self.ACTIVE_POLL_INTERVAL)
                else:
                    await asyncio.sleep(self.IDLE_POLL_INTERVAL)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in settlement loop: {e}")
                await asyncio.sleep(self.ERROR_BACKOFF_INTERVAL)
    
    async def _has_active_games(self) -> bool:
        """Check if any games are LIVE or recently FINAL (within last hour)."""
        try:
            async with AsyncSessionLocal() as db:
                cutoff = datetime.utcnow() - timedelta(hours=1)
                result = await db.execute(
                    select(Game.id).where(
                        and_(
                            Game.status.in_(["LIVE", "FINAL"]),
                            Game.start_time >= cutoff,
                        )
                    ).limit(1)
                )
                return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking for active games: {e}")
            return False
    
    async def _process_settlements(self):
        """Process all pending settlements."""
        async with AsyncSessionLocal() as db:
            settlement_service = SettlementService(db)
            
            try:
                # First, settle legs for games that just went FINAL
                # (games that went FINAL in the last hour and haven't been processed)
                cutoff = datetime.utcnow() - timedelta(hours=1)
                result = await db.execute(
                    select(Game).where(
                        and_(
                            Game.status == "FINAL",
                            Game.start_time >= cutoff,
                        )
                    )
                )
                final_games = result.scalars().all()
                
                for game in final_games:
                    try:
                        legs_settled = await settlement_service.settle_parlay_legs_for_game(game.id)
                        if legs_settled > 0:
                            logger.info(f"Settled {legs_settled} legs for game {game.id}")
                    except Exception as e:
                        logger.error(f"Error settling legs for game {game.id}: {e}")
                        continue
                
                # Then, update parlay statuses based on leg results
                stats = await settlement_service.settle_all_pending_parlays()
                
                if stats.parlays_settled > 0:
                    logger.info(
                        f"Settlement run: {stats.parlays_settled} parlays settled "
                        f"({stats.parlays_won} won, {stats.parlays_lost} lost)"
                    )
                
                # Update heartbeat
                await self._update_heartbeat(db, stats)
            
            except Exception as e:
                logger.error(f"Error in settlement processing: {e}")
                await db.rollback()
    
    async def _update_heartbeat(self, db, stats):
        """Update settlement worker heartbeat."""
        try:
            from app.models.system_heartbeat import SystemHeartbeat
            from sqlalchemy import select
            
            result = await db.execute(
                select(SystemHeartbeat).where(SystemHeartbeat.name == "settlement_worker")
            )
            heartbeat = result.scalar_one_or_none()
            
            if heartbeat:
                heartbeat.last_beat_at = datetime.utcnow()
                heartbeat.meta = {
                    "parlays_settled": stats.parlays_settled,
                    "parlays_won": stats.parlays_won,
                    "parlays_lost": stats.parlays_lost,
                }
            else:
                heartbeat = SystemHeartbeat(
                    name="settlement_worker",
                    last_beat_at=datetime.utcnow(),
                    meta={
                        "parlays_settled": stats.parlays_settled,
                        "parlays_won": stats.parlays_won,
                        "parlays_lost": stats.parlays_lost,
                    },
                )
                db.add(heartbeat)
            
            await db.commit()
        
        except Exception as e:
            logger.error(f"Error updating settlement heartbeat: {e}")


# Global worker instance
_worker = None


def get_settlement_worker() -> SettlementWorker:
    """Get the global SettlementWorker instance."""
    global _worker
    if _worker is None:
        _worker = SettlementWorker()
    return _worker


async def start_settlement_worker():
    """Start the settlement worker."""
    worker = get_settlement_worker()
    await worker.start()


async def stop_settlement_worker():
    """Stop the settlement worker."""
    worker = get_settlement_worker()
    await worker.stop()
