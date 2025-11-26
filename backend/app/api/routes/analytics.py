"""Analytics routes for parlay performance tracking"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.parlay_tracker import ParlayTrackerService

router = APIRouter()


class PerformanceStatsResponse(BaseModel):
    """Performance statistics response"""
    total_parlays: int
    hits: int
    misses: int
    hit_rate: float
    avg_predicted_prob: float
    avg_actual_prob: float
    avg_calibration_error: float


@router.get("/performance", response_model=PerformanceStatsResponse)
async def get_performance_stats(
    risk_profile: Optional[str] = Query(None, description="Filter by risk profile"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get parlay performance statistics
    
    Returns aggregated stats for resolved parlays
    """
    tracker = ParlayTrackerService(db)
    stats = await tracker.get_parlay_performance_stats(
        risk_profile=risk_profile,
        start_date=start_date,
        end_date=end_date
    )
    
    return PerformanceStatsResponse(**stats)


@router.get("/my-parlays")
async def get_my_parlay_history(
    limit: int = Query(50, ge=1, le=100, description="Number of parlays to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's parlay history"""
    tracker = ParlayTrackerService(db)
    parlays = await tracker.get_user_parlay_history(
        user_id=str(current_user.id),
        limit=limit
    )
    
    # Convert to response format
    return [
        {
            "id": str(p.id),
            "num_legs": p.num_legs,
            "risk_profile": p.risk_profile,
            "parlay_hit_prob": float(p.parlay_hit_prob),
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in parlays
    ]

