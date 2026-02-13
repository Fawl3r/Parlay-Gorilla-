"""Ops endpoints: job status, runbook helpers, public Safety Mode snapshot."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core import telemetry
from app.core.safety_mode import get_safety_snapshot
from app.database.session import AsyncSessionLocal
from app.repositories.scheduler_job_run_repository import SchedulerJobRunRepository

router = APIRouter()


@router.get("/safety")
async def ops_safety(request: Request):
    """Public Safety Mode snapshot (state, reasons, telemetry, events). No auth. For frontend banner."""
    try:
        await telemetry.load_critical_from_redis()
    except Exception:
        pass
    snap = get_safety_snapshot()
    try:
        await telemetry.save_critical_to_redis(snap)
    except Exception:
        pass
    return snap


@router.get("/jobs")
async def ops_jobs(request: Request):
    """
    Last run status for each scheduler job.
    Returns: job_name, last_run_at, duration_ms, status, error_snippet.
    """
    try:
        async with AsyncSessionLocal() as db:
            repo = SchedulerJobRunRepository(db)
            jobs = await repo.get_all()
        body = {"jobs": jobs}
        if hasattr(request, "state") and getattr(request.state, "request_id", None):
            body["request_id"] = request.state.request_id
        return JSONResponse(content=body)
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)[:500],
                "jobs": [],
                "request_id": getattr(request.state, "request_id", None) if hasattr(request, "state") else None,
            },
            status_code=500,
        )
