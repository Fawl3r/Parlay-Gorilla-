"""Scheduler job: API-Sports quota-safe refresh (fixtures, standings, teams, rosters, injuries)."""

from __future__ import annotations

import logging
import time

from app.services.apisports.quota_manager import get_quota_manager
from app.services.sports_refresh_service import run_apisports_refresh

logger = logging.getLogger(__name__)


class ApisportsRefreshJob:
    """Background job to refresh API-Sports cache. Runs in scheduler only. Logs structured summary."""

    async def run(self) -> None:
        """Run the API-Sports refresh pipeline. Never blocks user requests."""
        start = time.perf_counter()
        try:
            quota = get_quota_manager()
            remaining_before = await quota.remaining_async()
            if remaining_before <= 0:
                logger.info("[SCHEDULER] API-Sports refresh skipped: quota exhausted (remaining=%s)", remaining_before)
                return
            summary = await run_apisports_refresh()
            used = summary.get("used", 0)
            remaining_after = summary.get("remaining", 0)
            refreshed = summary.get("refreshed") or {}
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "[SCHEDULER] API-Sports refresh: used=%s remaining=%s duration_ms=%s refreshed=%s",
                used,
                remaining_after,
                duration_ms,
                refreshed,
                extra={
                    "used": used,
                    "remaining_after": remaining_after,
                    "duration_ms": duration_ms,
                    **refreshed,
                },
            )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.exception("[SCHEDULER] API-Sports refresh failed after %s ms: %s", duration_ms, e)
