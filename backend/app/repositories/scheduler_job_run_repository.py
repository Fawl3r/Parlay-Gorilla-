"""Record and query scheduler job run status for /ops/jobs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduler_job_run import SchedulerJobRun


def _truncate_error(s: Optional[str], max_len: int = 2000) -> Optional[str]:
    if not s:
        return None
    return s[:max_len] if len(s) > max_len else s


class SchedulerJobRunRepository:
    """Upsert last run per job; list all for ops."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def record(
        self,
        job_name: str,
        status: str,
        duration_ms: Optional[int] = None,
        error_snippet: Optional[str] = None,
        run_stats: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record or update last run for job_name (portable SQLite/Postgres). run_stats e.g. injuries_* for /ops/jobs."""
        now = datetime.now(timezone.utc)
        result = await self._db.execute(
            select(SchedulerJobRun).where(SchedulerJobRun.job_name == job_name)
        )
        row = result.scalar_one_or_none()
        if row:
            row.last_run_at = now
            row.duration_ms = duration_ms
            row.status = status
            row.error_snippet = _truncate_error(error_snippet)
            if run_stats is not None and hasattr(row, "run_stats"):
                row.run_stats = run_stats
        else:
            self._db.add(
                SchedulerJobRun(
                    job_name=job_name,
                    last_run_at=now,
                    duration_ms=duration_ms,
                    status=status,
                    error_snippet=_truncate_error(error_snippet),
                    run_stats=run_stats,
                )
            )
        await self._db.commit()

    async def get_all(self) -> List[dict[str, Any]]:
        """Return last run for each job (for /ops/jobs)."""
        result = await self._db.execute(
            select(SchedulerJobRun).order_by(SchedulerJobRun.job_name)
        )
        rows = result.scalars().all()
        return [
            {
                "job_name": r.job_name,
                "last_run_at": r.last_run_at.isoformat() if r.last_run_at else None,
                "duration_ms": r.duration_ms,
                "status": r.status,
                "error_snippet": r.error_snippet,
                "run_stats": getattr(r, "run_stats", None),
            }
            for r in rows
        ]
