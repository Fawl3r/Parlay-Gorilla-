"""System status endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.system_heartbeat import SystemHeartbeat
from app.models.parlay_feed_event import ParlayFeedEvent
from app.schemas.system import SystemStatusResponse

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    db: AsyncSession = Depends(get_db),
):
    """Get system status for proof of checking.
    
    Returns:
    - scraper_last_beat_at
    - settlement_last_beat_at
    - games_updated_last_run
    - parlays_settled_today
    - last_score_sync_at
    """
    try:
        # Get scraper heartbeat
        result = await db.execute(
            select(SystemHeartbeat).where(SystemHeartbeat.name == "scraper_worker")
        )
        scraper_heartbeat = result.scalar_one_or_none()
        scraper_last_beat_at = scraper_heartbeat.last_beat_at.isoformat() if scraper_heartbeat else None
        games_updated_last_run = scraper_heartbeat.meta.get("games_updated", 0) if scraper_heartbeat and scraper_heartbeat.meta else 0
        
        # Get settlement heartbeat
        result = await db.execute(
            select(SystemHeartbeat).where(SystemHeartbeat.name == "settlement_worker")
        )
        settlement_heartbeat = result.scalar_one_or_none()
        settlement_last_beat_at = settlement_heartbeat.last_beat_at.isoformat() if settlement_heartbeat else None
        
        # Count parlays settled today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(func.count(ParlayFeedEvent.id)).where(
                and_(
                    ParlayFeedEvent.event_type.in_(["PARLAY_WON", "PARLAY_LOST"]),
                    ParlayFeedEvent.created_at >= today_start,
                )
            )
        )
        parlays_settled_today = result.scalar() or 0
        
        # Get last score sync time (from scraper heartbeat meta)
        last_score_sync_at = scraper_last_beat_at
        
        return SystemStatusResponse(
            scraper_last_beat_at=scraper_last_beat_at,
            settlement_last_beat_at=settlement_last_beat_at,
            games_updated_last_run=games_updated_last_run,
            parlays_settled_today=parlays_settled_today,
            last_score_sync_at=last_score_sync_at,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching system status: {str(e)}")
