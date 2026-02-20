"""Admin API-Sports: quota status and manual refresh. Never returns 500."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.admin_safe import SAFE_APISPORTS_QUOTA, SAFE_APISPORTS_REFRESH
from app.models.user import User
from app.services.apisports.quota_manager import get_quota_manager
from app.services.sports_refresh_service import run_apisports_refresh
from .auth import require_admin

logger = logging.getLogger(__name__)
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
    """Return API-Sports quota. Returns safe defaults on error."""
    try:
        quota = get_quota_manager()
        used = await quota.used_today_async()
        remaining = await quota.remaining_async()
        circuit_open = await quota.is_circuit_open()
        daily_limit = getattr(quota, "_daily_limit", 100)
        logger.info("admin.endpoint.success", extra={"endpoint": "apisports.quota"})
        return QuotaResponse(used_today=used, remaining=remaining, circuit_open=circuit_open, daily_limit=daily_limit)
    except Exception as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "apisports.quota", "error": str(e)}, exc_info=True)
        return QuotaResponse(**SAFE_APISPORTS_QUOTA)


@router.post("/refresh", response_model=RefreshResponse)
async def trigger_apisports_refresh(
    admin: User = Depends(require_admin),
):
    """Trigger API-Sports refresh job. Returns safe body on error."""
    try:
        summary = await run_apisports_refresh()
        logger.info("admin.endpoint.success", extra={"endpoint": "apisports.refresh"})
        return RefreshResponse(
            used=summary.get("used", 0),
            remaining=summary.get("remaining", 0),
            refreshed=summary.get("refreshed", {}),
        )
    except Exception as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "apisports.refresh", "error": str(e)}, exc_info=True)
        return RefreshResponse(**SAFE_APISPORTS_REFRESH)
