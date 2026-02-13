"""Admin endpoint: Safety Mode snapshot (state, reasons, telemetry, events)."""

from fastapi import APIRouter, Depends

from app.core import telemetry
from app.core.safety_mode import get_safety_snapshot
from app.models.user import User
from .auth import require_admin

router = APIRouter()


@router.get("/safety")
async def get_safety(
    admin: User = Depends(require_admin),
):
    """Return current Safety Mode state, reasons, telemetry, and event ring buffer (no secrets)."""
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
