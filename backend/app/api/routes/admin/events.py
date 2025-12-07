"""
Admin events API routes.

Provides event analytics:
- Query events
- Get event counts
- Traffic analytics
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.core.dependencies import get_db
from app.models.user import User
from app.services.event_tracking_service import EventTrackingService
from .auth import require_admin

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
    """
    List events with filters.
    """
    service = EventTrackingService(db)
    
    events = await service.get_events(
        event_type=event_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    
    return [
        EventResponse(
            id=str(e.id),
            event_type=e.event_type,
            user_id=str(e.user_id) if e.user_id else None,
            session_id=e.session_id,
            metadata=e.metadata_,
            page_url=e.page_url,
            referrer=e.referrer,
            created_at=e.created_at.isoformat() if e.created_at else "",
        )
        for e in events
    ]


@router.get("/counts")
async def get_event_counts(
    time_range: str = Query("7d", regex="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get event counts by type.
    """
    now = datetime.utcnow()
    ranges = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
    }
    
    start_date = now - ranges.get(time_range, timedelta(days=7))
    
    service = EventTrackingService(db)
    counts = await service.get_event_counts(start_date, now)
    
    return {
        "time_range": time_range,
        "counts": counts,
    }


@router.get("/traffic", response_model=TrafficMetrics)
async def get_traffic_metrics(
    time_range: str = Query("7d", regex="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get traffic and SEO metrics.
    """
    now = datetime.utcnow()
    ranges = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
    }
    
    start_date = now - ranges.get(time_range, timedelta(days=7))
    
    service = EventTrackingService(db)
    
    unique_sessions = await service.get_unique_sessions(start_date, now)
    top_pages = await service.get_top_pages(start_date, now)
    referrer_breakdown = await service.get_referrer_breakdown(start_date, now)
    event_counts = await service.get_event_counts(start_date, now)
    
    return TrafficMetrics(
        unique_sessions=unique_sessions,
        top_pages=top_pages,
        referrer_breakdown=referrer_breakdown,
        event_counts=event_counts,
    )


@router.get("/parlays")
async def get_parlay_events(
    parlay_type: Optional[str] = Query(None, description="Filter by parlay type"),
    min_legs: Optional[int] = Query(None, ge=1),
    max_legs: Optional[int] = Query(None, le=20),
    time_range: str = Query("7d", regex="^(24h|7d|30d|90d)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get parlay-specific events.
    """
    now = datetime.utcnow()
    ranges = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
    }
    
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
    
    return [
        {
            "id": str(e.id),
            "parlay_type": e.parlay_type,
            "legs_count": e.legs_count,
            "expected_value": e.expected_value,
            "combined_odds": e.combined_odds,
            "hit_probability": e.hit_probability,
            "build_method": e.build_method,
            "was_saved": e.was_saved,
            "created_at": e.created_at.isoformat() if e.created_at else "",
        }
        for e in events
    ]

