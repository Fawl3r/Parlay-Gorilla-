"""Settlement worker for processing parlay settlements."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from app.database.session import AsyncSessionLocal
from app.services.settlement.settlement_service import SettlementService
from sqlalchemy import select, and_, func
from app.models.game import Game

logger = logging.getLogger(__name__)


class SettlementWorker:
    """Background worker for settling parlays."""
    
    # Smart cadence: faster during active games, slower otherwise
    ACTIVE_POLL_INTERVAL = 90  # 1.5 minutes during active games
    IDLE_POLL_INTERVAL = 300  # 5 minutes when no active games
    ERROR_BACKOFF_INTERVAL = 60  # seconds after error
    
    # Circuit breaker settings
    MAX_CONSECUTIVE_ERRORS = 5  # Open circuit after this many consecutive errors
    CIRCUIT_RESET_TIMEOUT = 300  # 5 minutes before attempting to close circuit
    
    # Rate limiting
    MAX_GAMES_PER_CYCLE = 100  # Process max 100 games per settlement cycle
    
    def __init__(self):
        self.running = False
        self._task = None
        self._consecutive_errors = 0
        self._circuit_open = False
        self._circuit_open_since = None
        self._last_error_time = None
    
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
        """Main polling loop with smart cadence and circuit breaker."""
        while self.running:
            try:
                # Check circuit breaker
                if self._circuit_open:
                    if self._circuit_open_since:
                        elapsed = (datetime.utcnow() - self._circuit_open_since).total_seconds()
                        if elapsed >= self.CIRCUIT_RESET_TIMEOUT:
                            logger.info(
                                f"SettlementWorker: Circuit breaker timeout reached, attempting to close circuit"
                            )
                            self._circuit_open = False
                            self._consecutive_errors = 0
                            self._circuit_open_since = None
                        else:
                            logger.warning(
                                f"SettlementWorker: Circuit breaker is OPEN, skipping settlement cycle "
                                f"(will retry in {self.CIRCUIT_RESET_TIMEOUT - elapsed:.0f}s)"
                            )
                            await asyncio.sleep(self.IDLE_POLL_INTERVAL)
                            continue
                    else:
                        self._circuit_open_since = datetime.utcnow()
                        await asyncio.sleep(self.IDLE_POLL_INTERVAL)
                        continue
                
                # Check if any games are LIVE or recently FINAL
                has_active_games = await self._has_active_games()
                
                # Process settlements
                await self._process_settlements()
                
                # Reset error count on successful run
                if self._consecutive_errors > 0:
                    logger.info(f"SettlementWorker: Successful run, resetting error count (was {self._consecutive_errors})")
                    self._consecutive_errors = 0
                
                # Wait based on activity
                if has_active_games:
                    await asyncio.sleep(self.ACTIVE_POLL_INTERVAL)
                else:
                    await asyncio.sleep(self.IDLE_POLL_INTERVAL)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._consecutive_errors += 1
                self._last_error_time = datetime.utcnow()
                
                logger.error(
                    f"SettlementWorker: Error in settlement loop (consecutive errors: {self._consecutive_errors}): {e}",
                    exc_info=True
                )
                
                # Open circuit breaker if too many consecutive errors
                if self._consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                    self._circuit_open = True
                    self._circuit_open_since = datetime.utcnow()
                    logger.critical(
                        f"SettlementWorker: Circuit breaker OPENED after {self._consecutive_errors} consecutive errors. "
                        f"Settlement processing paused for {self.CIRCUIT_RESET_TIMEOUT}s"
                    )
                    try:
                        from app.services.alerting import get_alerting_service
                        from app.core.config import settings
                        await get_alerting_service().emit(
                            "settlement.circuit_breaker_open",
                            "critical",
                            {
                                "environment": getattr(settings, "environment", "unknown"),
                                "consecutive_errors": self._consecutive_errors,
                                "error_type": type(e).__name__,
                                "error_message": str(e)[:500],
                            },
                        )
                    except Exception as alert_err:
                        logger.debug("SettlementWorker: alert emit failed: %s", alert_err)

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
        """Process all pending settlements with rate limiting."""
        async with AsyncSessionLocal() as db:
            settlement_service = SettlementService(db)
            
            try:
                # Settle legs for ALL FINAL games with pending legs; do NOT assume date-based completion.
                # Late games (delayed start, next-day finish) are included by using a wide window.
                # Duplicate settlement is prevented: we only update PENDING/LIVE legs; re-run is no-op.
                cutoff = datetime.utcnow() - timedelta(days=30)
                result = await db.execute(
                    select(Game).where(
                        and_(
                            Game.status == "FINAL",
                            Game.start_time >= cutoff,
                        )
                    ).limit(self.MAX_GAMES_PER_CYCLE)  # Rate limiting per cycle
                )
                final_games = result.scalars().all()
                
                if len(final_games) >= self.MAX_GAMES_PER_CYCLE:
                    logger.warning(
                        f"SettlementWorker: Rate limit reached, processing {self.MAX_GAMES_PER_CYCLE} games "
                        f"(more may be pending)"
                    )
                
                games_processed = 0
                total_legs_settled = 0
                
                for game in final_games:
                    try:
                        legs_settled = await settlement_service.settle_parlay_legs_for_game(game.id)
                        if legs_settled > 0:
                            logger.info(f"SettlementWorker: Settled {legs_settled} legs for game {game.id}")
                            total_legs_settled += legs_settled
                        games_processed += 1
                    except Exception as e:
                        logger.error(
                            f"SettlementWorker: Error settling legs for game {game.id}: {e}",
                            exc_info=True
                        )
                        # Continue processing other games
                        continue
                
                if games_processed > 0:
                    logger.info(
                        f"SettlementWorker: Processed {games_processed} FINAL games, "
                        f"settled {total_legs_settled} legs total"
                    )

                # Void legs only for games that will NEVER complete (no_contest, cancelled).
                # Do NOT auto-void postponed/suspended: they may resume (e.g. 2 days later).
                # Postponed/suspended are only voided if: (1) still non-final after 7+ days (optional job),
                # or (2) provider later marks them cancelled. See docs/deploy/edge_case_settlement.md.
                VOID_ONLY_STATUSES = ("no_contest", "cancelled")
                void_cutoff = datetime.utcnow() - timedelta(days=30)
                void_result = await db.execute(
                    select(Game.id).where(
                        and_(
                            func.lower(Game.status).in_(VOID_ONLY_STATUSES),
                            Game.start_time >= void_cutoff,
                        )
                    ).limit(50)
                )
                void_game_ids = [r[0] for r in void_result.fetchall()]
                for gid in void_game_ids:
                    try:
                        voided = await settlement_service.void_legs_for_non_resumed_game(
                            gid, reason="game_no_contest_or_cancelled"
                        )
                        if voided > 0:
                            total_legs_settled += voided
                    except Exception as void_err:
                        logger.warning("SettlementWorker: void legs for game %s: %s", gid, void_err)

                # Then, update parlay statuses based on leg results
                stats = await settlement_service.settle_all_pending_parlays()

                # Stat correction: re-check FINAL results once within 72h after first settlement
                reeval_count = await settlement_service.re_eval_stat_corrections()
                if reeval_count > 0:
                    logger.warning("SettlementWorker: Stat correction re-eval applied to %s leg(s)", reeval_count)
                
                if stats.parlays_settled > 0:
                    logger.info(
                        f"SettlementWorker: Settlement run completed - {stats.parlays_settled} parlays settled "
                        f"({stats.parlays_won} won, {stats.parlays_lost} lost)"
                    )
                elif games_processed == 0:
                    logger.debug("SettlementWorker: No FINAL games to process")
                
                # Update heartbeat
                await self._update_heartbeat(db, stats)
            
            except Exception as e:
                logger.error(
                    f"SettlementWorker: Error in settlement processing: {e}",
                    exc_info=True
                )
                try:
                    from app.services.alerting import get_alerting_service
                    from app.core.config import settings
                    await get_alerting_service().emit(
                        "settlement.failure",
                        "error",
                        {
                            "environment": getattr(settings, "environment", "unknown"),
                            "error_type": type(e).__name__,
                            "error_message": str(e)[:500],
                        },
                    )
                except Exception as alert_err:
                    logger.debug("SettlementWorker: alert emit failed: %s", alert_err)
                try:
                    await db.rollback()
                except Exception as rollback_error:
                    logger.error(
                        f"SettlementWorker: Error during rollback: {rollback_error}",
                        exc_info=True
                    )
                # Re-raise to trigger circuit breaker logic
                raise
    
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
