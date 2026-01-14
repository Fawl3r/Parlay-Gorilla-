"""Scheduler job for auto-resolving saved parlays."""

from __future__ import annotations

from app.database.session import AsyncSessionLocal
from app.services.saved_parlay_tracker import SavedParlayTrackerService


class SavedParlayResolutionJob:
    """Background job to automatically resolve saved parlay outcomes."""

    async def run(self) -> None:
        """Run the saved parlay resolution job."""
        async with AsyncSessionLocal() as db:
            try:
                tracker = SavedParlayTrackerService(db)
                resolved = await tracker.auto_resolve_saved_parlays(limit=200)
                if resolved > 0:
                    print(f"[SCHEDULER] Auto-resolved {resolved} saved parlays")
            except Exception as e:
                print(f"[SCHEDULER] Error auto-resolving saved parlays: {e}")
                import traceback

                traceback.print_exc()

