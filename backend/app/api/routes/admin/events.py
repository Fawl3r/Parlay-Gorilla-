"""
Admin events API routes. Never returns 500; missing tables return safe fallbacks.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, ProgrammingError
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.core.dependencies import get_db
from app.core.admin_safe import SAFE_EVENTS_LIST, SAFE_EVENTS_COUNTS, SAFE_EVENTS_TRAFFIC
from app.models.user import User
from app.services.event_tracking_service import EventTrackingService
from .auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter()


class EventResponse(BaseModel):
    """Event response model."""
    id: str
    event_type: str
    user_id: Optional[str]
    session_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    page_url: Optional[str]
    referrer: Optional[str]
    created_at: str


class TrafficMetrics(BaseModel):
    """Traffic metrics response."""
    unique_sessions: int
    top_pages: List[Dict[str, Any]]
    referrer_breakdown: Dict[str, int]
    event_counts: Dict[str, int]


@router.get("")
async def list_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """List events with filters. Returns [] on DB/table errors."""
    try:
        service = EventTrackingService(db)
        events = await service.get_events(
            event_type=event_type,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        logger.info("admin.endpoint.success", extra={"endpoint": "events.list"})
        return [
            EventResponse(
                id=str(e.id),
                event_type=e.event_type or "",
                user_id=str(e.user_id) if e.user_id else None,
                session_id=e.session_id,
                metadata=e.metadata_,
                page_url=e.page_url,
                referrer=e.referrer,
                created_at=e.created_at.isoformat() if e.created_at else "",
            )
            for e in events
        ]
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "events.list", "error": str(e)}, exc_info=True)
        return list(SAFE_EVENTS_LIST)


@router.get("/counts")
async def get_event_counts(
    time_range: str = Query("7d", pattern="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get event counts by type. Returns safe empty on DB/table errors."""
    try:
        now = datetime.utcnow()
        ranges = {"24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30), "90d": timedelta(days=90)}
        start_date = now - ranges.get(time_range, timedelta(days=7))
        service = EventTrackingService(db)
        counts = await service.get_event_counts(start_date, now)
        logger.info("admin.endpoint.success", extra={"endpoint": "events.counts"})
        return {"time_range": time_range, "counts": counts or {}}
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "events.counts", "error": str(e)}, exc_info=True)
        return {"time_range": time_range, "counts": dict(SAFE_EVENTS_COUNTS)}


@router.get("/traffic", response_model=TrafficMetrics)
async def get_traffic_metrics(
    time_range: str = Query("7d", pattern="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get traffic and SEO metrics. Returns safe zeros on DB/table errors."""
    try:
        now = datetime.utcnow()
        ranges = {"24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30), "90d": timedelta(days=90)}
        start_date = now - ranges.get(time_range, timedelta(days=7))
        service = EventTrackingService(db)
        unique_sessions = await service.get_unique_sessions(start_date, now)
        top_pages = await service.get_top_pages(start_date, now)
        referrer_breakdown = await service.get_referrer_breakdown(start_date, now)
        event_counts = await service.get_event_counts(start_date, now)
        logger.info("admin.endpoint.success", extra={"endpoint": "events.traffic"})
        return TrafficMetrics(
            unique_sessions=unique_sessions or 0,
            top_pages=top_pages or [],
            referrer_breakdown=referrer_breakdown or {},
            event_counts=event_counts or {},
        )
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "events.traffic", "error": str(e)}, exc_info=True)
        return TrafficMetrics(**SAFE_EVENTS_TRAFFIC)


@router.get("/parlays")
async def get_parlay_events(
    parlay_type: Optional[str] = Query(None, description="Filter by parlay type"),
    min_legs: Optional[int] = Query(None, ge=1),
    max_legs: Optional[int] = Query(None, le=20),
    time_range: str = Query("7d", pattern="^(24h|7d|30d|90d)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get parlay-specific events. Returns [] on DB/table errors."""
    try:
        now = datetime.utcnow()
        ranges = {"24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30), "90d": timedelta(days=90)}
        start_date = now - ranges.get(time_range, timedelta(days=7))
        service = EventTrackingService(db)
        events = await service.get_parlay_events(
            parlay_type=parlay_type,
            start_date=start_date,
            end_date=now,
            min_legs=min_legs,
            max_legs=max_legs,
            limit=limit,
            offset=offset,
        )
        logger.info("admin.endpoint.success", extra={"endpoint": "events.parlays"})
        return [
            {
                "id": str(e.id),
                "parlay_type": getattr(e, "parlay_type", "") or "",
                "legs_count": getattr(e, "legs_count", 0) or 0,
                "expected_value": getattr(e, "expected_value", None),
                "combined_odds": getattr(e, "combined_odds", None),
                "hit_probability": getattr(e, "hit_probability", None),
                "build_method": getattr(e, "build_method", None),
                "was_saved": getattr(e, "was_saved", False),
                "created_at": e.created_at.isoformat() if getattr(e, "created_at", None) else "",
            }
            for e in (events or [])
        ]
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "events.parlays", "error": str(e)}, exc_info=True)
        return list(SAFE_EVENTS_LIST)

