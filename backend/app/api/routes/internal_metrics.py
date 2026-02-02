"""
Internal AI Picks Health dashboard endpoint.

Gated by:
- Admin auth (Bearer token, user is admin), OR
- INTERNAL_METRICS_ENABLED=true and X-Internal-Key header matching INTERNAL_METRICS_KEY.

Returns 404 (not 401) when unauthorized to avoid exposing existence.
"""

from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.dependencies import get_db, get_optional_user
from app.core.config import settings
from app.models.user import User
from app.services.event_tracking_service import EventTrackingService

router = APIRouter()


def _is_admin(user: Optional[User]) -> bool:
    return user is not None and user.role == "admin"


async def require_internal_or_admin(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
) -> None:
    """
    Allow access if user is admin, or if internal metrics are enabled and X-Internal-Key matches.
    Otherwise raise 404 (not 401) to avoid exposing endpoint existence.
    """
    if _is_admin(current_user):
        return
    if settings.internal_metrics_enabled and settings.internal_metrics_key:
        key = request.headers.get("X-Internal-Key")
        if key and key == settings.internal_metrics_key:
            return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.get("/ai-picks-health")
async def get_ai_picks_health(
    days: int = Query(7, ge=1, le=90, description="Window in days"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_internal_or_admin),
):
    """
    Return aggregated AI Picks health metrics for the last N days.
    Used by internal dashboard only. Gated by admin or env + secret header.
    """
    service = EventTrackingService(db)
    return await service.get_ai_picks_health_aggregates(days=days)
