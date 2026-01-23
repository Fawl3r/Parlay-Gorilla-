"""Feed endpoints for marquee and win wall."""

from __future__ import annotations

from typing import List, Literal, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.parlay_feed_event import ParlayFeedEvent
from app.schemas.feed import FeedEventResponse, WinWallResponse

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/marquee", response_model=List[FeedEventResponse])
async def get_marquee_feed(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of events to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get recent feed events for marquee display.
    
    Returns events sorted by created_at DESC, including:
    - GAME_LIVE
    - GAME_FINAL
    - PARLAY_WON
    - PARLAY_LOST
    - LEG_WON
    - LEG_LOST
    """
    try:
        result = await db.execute(
            select(ParleyFeedEvent)
            .order_by(ParleyFeedEvent.created_at.desc())
            .limit(limit)
        )
        events = result.scalars().all()
        
        return [
            FeedEventResponse(
                id=str(event.id),
                event_type=event.event_type,
                sport=event.sport,
                summary=event.summary,
                created_at=event.created_at.isoformat(),
                metadata=event.metadata or {},
            )
            for event in events
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching marquee feed: {str(e)}")


@router.get("/wins", response_model=List[WinWallResponse])
async def get_win_wall(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of wins to return"),
    type: Literal["AI", "CUSTOM", "ALL"] = Query("ALL", description="Filter by parlay type"),
    db: AsyncSession = Depends(get_db),
):
    """Get parlay wins for win wall display.
    
    Returns only PARLAY_WON events, filtered by type (AI/CUSTOM/ALL).
    """
    try:
        query = select(ParleyFeedEvent).where(
            ParleyFeedEvent.event_type == "PARLAY_WON"
        )
        
        if type != "ALL":
            # Filter by parlay_type in metadata
            if type == "AI":
                query = query.where(
                    func.jsonb_extract_path_text(ParleyFeedEvent.metadata, "parlay_type") == "AI"
                )
            elif type == "CUSTOM":
                query = query.where(
                    func.jsonb_extract_path_text(ParleyFeedEvent.metadata, "parlay_type") == "CUSTOM"
                )
        
        result = await db.execute(
            query
            .order_by(ParleyFeedEvent.created_at.desc())
            .limit(limit)
        )
        events = result.scalars().all()
        
        return [
            WinWallResponse(
                id=str(event.id),
                parlay_type=event.metadata.get("parlay_type", "UNKNOWN") if event.metadata else "UNKNOWN",
                legs_count=event.metadata.get("legs_count", 0) if event.metadata else 0,
                odds=event.metadata.get("odds", "+0") if event.metadata else "+0",
                user_alias=event.user_alias,
                settled_at=event.created_at.isoformat(),
                summary=event.summary,
            )
            for event in events
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching win wall: {str(e)}")
