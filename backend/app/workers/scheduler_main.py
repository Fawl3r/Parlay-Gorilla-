"""
Standalone scheduler process: sport/team/standings/injuries/roster refresh.

- Runs as separate process (systemd parlaygorilla-scheduler.service).
- Uses Redis lock to prevent concurrent runs.
- Records last_run_at, duration_ms, status, error_snippet per job (for /ops/jobs).
- One job failure does not kill the process; logs and alerts via Telegram.
- Idempotent, respects TTL skip and quota budget (inside run_apisports_refresh).
"""

from __future__ import annotations

import asyncio
import logging
import sys
import time
import traceback
from datetime import datetime, timezone, timedelta

from app.core.config import settings
from app.database.session import AsyncSessionLocal
from app.repositories.scheduler_job_run_repository import SchedulerJobRunRepository
from app.services.redis.redis_client_provider import get_redis_provider
from app.services.redis.redis_distributed_lock import RedisDistributedLock

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("scheduler_main")

# Job name -> interval in seconds
# Sport state every 6h; daily pass for team catalog, standings, injuries, roster (same pipeline, quota-aware).
JOB_INTERVALS = {
    "apisports_refresh": 6 * 3600,   # 6 hours — sport state
    "apisports_daily": 24 * 3600,    # 24 hours — team catalog, standings, injuries, roster rotation
}
LOCK_KEY = "parlaygorilla:scheduler:run"
LOCK_TTL_SECONDS = 45 * 60  # 45 min
CYCLE_SLEEP_SECONDS = 60 * 60  # check every 1 hour


async def _get_last_run_at(db_session, job_name: str) -> datetime | None:
    from sqlalchemy import select
    from app.models.scheduler_job_run import SchedulerJobRun
    result = await db_session.execute(
        select(SchedulerJobRun.last_run_at).where(SchedulerJobRun.job_name == job_name)
    )
    return result.scalar_one_or_none()


async def _run_job(job_name: str) -> tuple[str, int | None, str | None, dict | None]:
    """Run a single job. Returns (status, duration_ms, error_snippet, run_stats)."""
    start = time.perf_counter()
    run_stats = None
    try:
        if job_name in ("apisports_refresh", "apisports_daily"):
            from app.services.sports_refresh_service import run_apisports_refresh
            summary = await run_apisports_refresh()
            logger.info(
                "[SCHEDULER] %s done: used=%s remaining=%s refreshed=%s",
                job_name,
                summary.get("used"),
                summary.get("remaining"),
                summary.get("refreshed"),
            )
            run_stats = summary.get("run_stats")
        else:
            raise ValueError(f"Unknown job: {job_name}")
        duration_ms = int((time.perf_counter() - start) * 1000)
        return ("success", duration_ms, None, run_stats)
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        err_snippet = f"{type(e).__name__}: {str(e)[:500]}"
        logger.exception("[SCHEDULER] Job %s failed: %s", job_name, e)
        try:
            from app.services.alerting import get_alerting_service
            from app.services.alerting.alerting_service import trim_stack_trace
            await get_alerting_service().emit(
                "scheduler.job_failure",
                "error",
                {
                    "service": "scheduler",
                    "job_name": job_name,
                    "request_id": f"sched-{job_name}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
                    "environment": getattr(settings, "environment", "unknown"),
                    "exception_type": type(e).__name__,
                    "message": str(e)[:500],
                    "stack_trace": trim_stack_trace(traceback.format_exc(), max_lines=30),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception as alert_err:
            logger.debug("Alert emit skipped: %s", alert_err)
        return ("failure", duration_ms, err_snippet, None)


async def _run_cycle() -> None:
    """Acquire lock, run due jobs, record results, release lock."""
    provider = get_redis_provider()
    if not provider.is_configured():
        logger.warning("[SCHEDULER] Redis not configured; skipping cycle")
        return
    client = provider.get_client()
    lock = RedisDistributedLock(client=client)
    handle = await lock.try_acquire(key=LOCK_KEY, ttl_seconds=LOCK_TTL_SECONDS)
    if not handle:
        logger.info("[SCHEDULER] Lock held by another process; skip cycle")
        return
    try:
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as db:
            repo = SchedulerJobRunRepository(db)
            for job_name, interval_sec in JOB_INTERVALS.items():
                last_run = await _get_last_run_at(db, job_name)
                due = last_run is None or (now - last_run).total_seconds() >= interval_sec
                if not due:
                    continue
                logger.info("[SCHEDULER] Running job: %s", job_name)
                status, duration_ms, error_snippet, run_stats = await _run_job(job_name)
                await repo.record(
                    job_name=job_name,
                    status=status,
                    duration_ms=duration_ms,
                    error_snippet=error_snippet,
                    run_stats=run_stats,
                )
                logger.info(
                    "[SCHEDULER] Job %s finished: status=%s duration_ms=%s",
                    job_name, status, duration_ms,
                )
    finally:
        await lock.release(handle)


async def main() -> None:
    """Loop: run cycle every CYCLE_SLEEP_SECONDS."""
    logger.info("[SCHEDULER] Standalone scheduler started; cycle_sleep=%ss", CYCLE_SLEEP_SECONDS)
    while True:
        try:
            await _run_cycle()
        except Exception as e:
            logger.exception("[SCHEDULER] Cycle error: %s", e)
        await asyncio.sleep(CYCLE_SLEEP_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
