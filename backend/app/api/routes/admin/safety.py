"""Admin endpoint: Safety Mode snapshot (state, reasons, telemetry, events)."""

import logging

from fastapi import APIRouter, Depends

from app.core import telemetry
from app.core.safety_mode import get_safety_snapshot
from app.core.admin_safe import SAFE_SAFETY
from app.models.user import User
from .auth import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/safety")
async def get_safety(
    admin: User = Depends(require_admin),
):
    """Return current Safety Mode state, reasons, telemetry, and event ring buffer. Never 500."""
    try:
        try:
            await telemetry.load_critical_from_redis()
        except Exception:
            pass
        snap = get_safety_snapshot()
        if not isinstance(snap, dict):
            return dict(SAFE_SAFETY)
        try:
            await telemetry.save_critical_to_redis(snap)
        except Exception:
            pass
        logger.info("admin.endpoint.success", extra={"endpoint": "safety"})
        return snap
    except Exception as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "safety", "error": str(e)}, exc_info=True)
        return dict(SAFE_SAFETY)
