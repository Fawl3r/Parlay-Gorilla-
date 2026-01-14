"""Scheduler job for syncing game results from ESPN."""

from __future__ import annotations

from app.database.session import AsyncSessionLocal
from app.services.game_results.espn_game_results_sync_service import EspnGameResultsSyncService


class GameResultsSyncJob:
    """Background job to sync completed game results from ESPN scoreboard."""

    async def run(self) -> None:
        """Run the game results sync job."""
        async with AsyncSessionLocal() as db:
            try:
                service = EspnGameResultsSyncService(db)
                synced = await service.sync_recent_games(lookback_days=3)
                if synced > 0:
                    print(f"[SCHEDULER] Synced {synced} game results from ESPN")
            except Exception as e:
                print(f"[SCHEDULER] Error syncing game results: {e}")
                import traceback

                traceback.print_exc()

