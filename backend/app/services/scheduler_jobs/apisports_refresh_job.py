"""Scheduler job: API-Sports quota-safe refresh (fixtures, standings)."""

from __future__ import annotations

import logging

from app.services.apisports.quota_manager import get_quota_manager
from app.services.sports_refresh_service import run_apisports_refresh

logger = logging.getLogger(__name__)


class ApisportsRefreshJob:
    """Background job to refresh API-Sports cache (fixtures, standings). Runs in scheduler only."""

    async def run(self) -> None:
        """Run the API-Sports refresh pipeline. Never blocks user requests."""
        try:
            quota = get_quota_manager()
            if await quota.remaining_async() <= 0:
                logger.info("[SCHEDULER] API-Sports quota exhausted, skip refresh")
                return
            summary = await run_apisports_refresh()
            used = summary.get("used", 0)
            remaining = summary.get("remaining", 0)
            if used > 0:
                logger.info(
                    "[SCHEDULER] API-Sports refresh: used=%s remaining=%s refreshed=%s",
                    used,
                    remaining,
                    summary.get("refreshed", {}),
                )
        except Exception as e:
            logger.exception("[SCHEDULER] API-Sports refresh failed: %s", e)
