"""Admin API-Sports: quota status and manual refresh (guarded)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.models.user import User
from app.services.apisports.quota_manager import get_quota_manager
from app.services.sports_refresh_service import run_apisports_refresh
from .auth import require_admin

router = APIRouter()


class QuotaResponse(BaseModel):
    used_today: int
    remaining: int
    circuit_open: bool
    daily_limit: int


class RefreshResponse(BaseModel):
    used: int
    remaining: int
    refreshed: dict


@router.get("/quota", response_model=QuotaResponse)
async def get_apisports_quota(
    admin: User = Depends(require_admin),
):
    """Return API-Sports quota: used today, remaining, circuit breaker status."""
    quota = get_quota_manager()
    used = await quota.used_today_async()
    remaining = await quota.remaining_async()
    circuit_open = await quota.is_circuit_open()
    daily_limit = getattr(quota, "_daily_limit", 100)
    return QuotaResponse(
        used_today=used,
        remaining=remaining,
        circuit_open=circuit_open,
        daily_limit=daily_limit,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def trigger_apisports_refresh(
    admin: User = Depends(require_admin),
):
    """Trigger API-Sports refresh job (quota-safe). Use sparingly."""
    summary = await run_apisports_refresh()
    return RefreshResponse(
        used=summary.get("used", 0),
        remaining=summary.get("remaining", 0),
        refreshed=summary.get("refreshed", {}),
    )
