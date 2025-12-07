"""
Public events API route.

Provides event tracking endpoint for analytics.
This is a public endpoint that tracks events from the frontend.
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.core.dependencies import get_db, get_optional_user
from app.models.user import User
from app.services.event_tracking_service import EventTrackingService

router = APIRouter()


class TrackEventRequest(BaseModel):
    """Request model for tracking an event."""
    event_type: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    page_url: Optional[str] = None
    referrer: Optional[str] = None


class TrackParlayEventRequest(BaseModel):
    """Request model for tracking a parlay event."""
    parlay_type: str  # safe, balanced, degen, custom
    legs_count: int
    session_id: Optional[str] = None
    parlay_id: Optional[str] = None
    sport_filters: Optional[list] = None
    expected_value: Optional[float] = None
    combined_odds: Optional[float] = None
    hit_probability: Optional[float] = None
    legs_breakdown: Optional[Dict[str, int]] = None
    was_saved: bool = False
    was_shared: bool = False
    build_method: Optional[str] = None


@router.post("/events")
async def track_event(
    request: TrackEventRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Track an analytics event.
    
    This endpoint is public but will attach user_id if authenticated.
    Rate limited to prevent abuse.
    
    Common event types:
    - view_analysis: User viewed a game analysis page
    - build_parlay: User opened the parlay builder
    - view_parlay_result: User viewed a generated parlay
    - click_upset_finder: User clicked the upset finder feature
    - page_view: General page view
    """
    # Validate event type
    allowed_events = [
        "view_analysis",
        "build_parlay",
        "view_parlay_result",
        "click_upset_finder",
        "page_view",
        "share_parlay",
        "save_parlay",
        "signup_start",
        "signup_complete",
        "login",
        "upgrade_click",
    ]
    
    if request.event_type not in allowed_events:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type. Allowed: {allowed_events}"
        )
    
    # Extract client info from request
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    referrer = request.referrer or http_request.headers.get("referer")
    
    service = EventTrackingService(db)
    
    event = await service.track_event(
        event_type=request.event_type,
        user_id=str(current_user.id) if current_user else None,
        session_id=request.session_id,
        metadata=request.metadata,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer,
        page_url=request.page_url,
    )
    
    return {
        "success": True,
        "event_id": str(event.id),
    }


@router.post("/events/parlay")
async def track_parlay_event(
    request: TrackParlayEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Track a parlay-specific event.
    
    Called when a user generates or interacts with a parlay.
    """
    # Validate parlay type
    allowed_types = ["safe", "balanced", "degen", "custom"]
    if request.parlay_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parlay type. Allowed: {allowed_types}"
        )
    
    service = EventTrackingService(db)
    
    event = await service.track_parlay_event(
        parlay_type=request.parlay_type,
        legs_count=request.legs_count,
        user_id=str(current_user.id) if current_user else None,
        session_id=request.session_id,
        parlay_id=request.parlay_id,
        sport_filters=request.sport_filters,
        expected_value=request.expected_value,
        combined_odds=request.combined_odds,
        hit_probability=request.hit_probability,
        legs_breakdown=request.legs_breakdown,
        was_saved=request.was_saved,
        was_shared=request.was_shared,
        build_method=request.build_method,
    )
    
    return {
        "success": True,
        "event_id": str(event.id),
    }

