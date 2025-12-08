"""
Live Game Sync Worker - Background process for real-time game updates.

Polls SportsRadar API for live game data every 15-20 seconds.
Triggers Telegram notifications for score changes and drive updates.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List

from app.database.session import AsyncSessionLocal
from app.services.live_game_service import LiveGameService
from app.services.telegram_bot_service import get_telegram_service
from app.models.live_game import LiveGame, LiveGameStatus

logger = logging.getLogger(__name__)


class LiveGameSyncWorker:
    """
    Background worker that polls live games and triggers updates.
    
    Features:
    - Polls every 15-20 seconds during active games
    - Sends Telegram notifications for:
      - Score changes
      - New drives (NFL)
      - Game endings
      - Halftime
    - Handles errors gracefully without crashing
    """
    
    DEFAULT_POLL_INTERVAL = 18  # seconds
    ERROR_BACKOFF_INTERVAL = 60  # seconds after error
    
    def __init__(self, poll_interval: int = DEFAULT_POLL_INTERVAL):
        """
        Initialize the worker.
        
        Args:
            poll_interval: Seconds between polls (default 18)
        """
        self.poll_interval = poll_interval
        self.running = False
        self.telegram = get_telegram_service()
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the background worker."""
        if self.running:
            logger.warning("LiveGameSyncWorker already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"LiveGameSyncWorker started (poll interval: {self.poll_interval}s)")
    
    async def stop(self):
        """Stop the background worker."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("LiveGameSyncWorker stopped")
    
    async def _run_loop(self):
        """Main polling loop."""
        while self.running:
            try:
                await self._poll_live_games()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in live game sync loop: {e}")
                # Back off on errors
                await asyncio.sleep(self.ERROR_BACKOFF_INTERVAL)
    
    async def _poll_live_games(self):
        """Poll all live games and process updates."""
        async with AsyncSessionLocal() as db:
            try:
                service = LiveGameService(db)
                
                # Get all in-progress games
                live_games = await service.get_all_live_games(include_recent_finals=False)
                
                if not live_games:
                    logger.debug("No live games to poll")
                    return
                
                logger.info(f"Polling {len(live_games)} live games")
                
                # Process each game
                for game in live_games:
                    await self._process_game_update(db, service, game)
                    
            except Exception as e:
                logger.error(f"Error polling live games: {e}")
    
    async def _process_game_update(
        self,
        db,
        service: LiveGameService,
        game: LiveGame
    ):
        """Process updates for a single game."""
        try:
            game_id = str(game.id)
            
            # Update game state
            updated_game, score_changed, status_changed = await service.update_live_game_state(game_id)
            
            if not updated_game:
                return
            
            # Sync drives (for NFL)
            new_drives = await service.sync_game_drives(game_id)
            
            # Send notifications
            await self._send_notifications(
                updated_game,
                score_changed,
                status_changed,
                new_drives
            )
            
        except Exception as e:
            logger.error(f"Error processing game {game.id}: {e}")
    
    async def _send_notifications(
        self,
        game: LiveGame,
        score_changed: bool,
        status_changed: bool,
        new_drives: list
    ):
        """Send Telegram notifications for game events."""
        
        # Check if Telegram is configured
        if not self.telegram.is_configured:
            return
        
        # Send notifications for new scoring drives
        for drive in new_drives:
            if drive.is_scoring_drive:
                try:
                    await self.telegram.send_drive_update(
                        team=drive.team,
                        result=drive.result or "score",
                        description=drive.description or "",
                        score_home=game.home_score,
                        score_away=game.away_score,
                        home_team=game.home_team,
                        away_team=game.away_team,
                    )
                except Exception as e:
                    logger.error(f"Error sending drive notification: {e}")
        
        # Send score update if score changed (but no drive notification sent)
        if score_changed and not any(d.is_scoring_drive for d in new_drives):
            try:
                await self.telegram.send_score_update(
                    home_team=game.home_team,
                    away_team=game.away_team,
                    home_score=game.home_score,
                    away_score=game.away_score,
                    period=game.period_name,
                    time_remaining=game.time_remaining,
                )
            except Exception as e:
                logger.error(f"Error sending score notification: {e}")
        
        # Send status change notifications
        if status_changed:
            try:
                if game.status == LiveGameStatus.final.value:
                    await self.telegram.send_final_update(
                        home_team=game.home_team,
                        away_team=game.away_team,
                        home_score=game.home_score,
                        away_score=game.away_score,
                        sport=game.sport,
                    )
                elif game.status == LiveGameStatus.halftime.value:
                    await self.telegram.send_halftime(
                        home_team=game.home_team,
                        away_team=game.away_team,
                        home_score=game.home_score,
                        away_score=game.away_score,
                    )
                elif game.status == LiveGameStatus.in_progress.value:
                    # Game just started
                    await self.telegram.send_game_start(
                        home_team=game.home_team,
                        away_team=game.away_team,
                        sport=game.sport,
                    )
            except Exception as e:
                logger.error(f"Error sending status notification: {e}")


# Global worker instance
_worker: Optional[LiveGameSyncWorker] = None


def get_live_game_sync_worker() -> LiveGameSyncWorker:
    """Get the global LiveGameSyncWorker instance."""
    global _worker
    if _worker is None:
        _worker = LiveGameSyncWorker()
    return _worker


async def start_live_game_worker():
    """Start the live game sync worker."""
    worker = get_live_game_sync_worker()
    await worker.start()


async def stop_live_game_worker():
    """Stop the live game sync worker."""
    worker = get_live_game_sync_worker()
    await worker.stop()


# Entry point for running as standalone process
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    async def main():
        worker = LiveGameSyncWorker()
        
        print("Starting LiveGameSyncWorker...")
        print("Press Ctrl+C to stop")
        
        await worker.start()
        
        try:
            # Run forever
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            print("\nStopping worker...")
            await worker.stop()
    
    asyncio.run(main())

