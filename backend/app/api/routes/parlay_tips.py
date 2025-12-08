"""
API Routes for Parlay Tips.

Endpoints:
- GET /api/parlay-tips - Get parlay building tips (personalized for premium)
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database.session import get_db
from app.core.dependencies import get_current_user_optional
from app.models.user import User
from app.services.parlay_tips_service import ParlayTipsService
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/api", tags=["parlay-tips"])


# ============= Response Models =============

class TipResponse(BaseModel):
    """Response model for a single tip."""
    id: str
    category: str
    title: str
    tip: str
    icon: str = "💡"


class ParlayTipsResponse(BaseModel):
    """Response model for parlay tips."""
    tier: str  # "free" or "premium"
    tips: List[TipResponse]
    personalized: bool
    message: Optional[str] = None
    profile_summary: Optional[str] = None
    upgrade_cta: bool = False
    upgrade_url: str = "/pricing"


# ============= Endpoints =============

@router.get(
    "/parlay-tips",
    response_model=ParlayTipsResponse,
    summary="Get parlay building tips",
    description="Returns parlay building tips. Premium users get AI-personalized tips."
)
async def get_parlay_tips(
    limit: int = Query(5, ge=1, le=10, description="Number of tips to return"),
    sport: Optional[str] = Query(None, description="Filter tips by sport"),
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Get parlay building tips.
    
    - **Free users**: Get generic, static tips
    - **Premium users**: Get AI-personalized tips based on betting history
    
    - **limit**: Number of tips to return (1-10)
    - **sport**: Optional sport filter (nfl, nba, nhl, mlb)
    """
    # Check if user is premium
    is_premium = False
    user_id = None
    
    if user:
        user_id = str(user.id)
        subscription_service = SubscriptionService(db)
        is_premium = await subscription_service.is_user_premium(user_id)
    
    # Get tips from service
    tips_service = ParlayTipsService(db)
    result = await tips_service.get_parlay_tips(
        user_id=user_id,
        is_premium=is_premium,
        limit=limit,
        sport=sport,
    )
    
    # Convert tips to response format
    tips = []
    for tip_data in result.get("tips", []):
        tips.append(TipResponse(
            id=tip_data.get("id", "tip"),
            category=tip_data.get("category", "general"),
            title=tip_data.get("title", "Tip"),
            tip=tip_data.get("tip", ""),
            icon=tip_data.get("icon", "💡"),
        ))
    
    return ParlayTipsResponse(
        tier=result.get("tier", "free"),
        tips=tips,
        personalized=result.get("personalized", False),
        message=result.get("message"),
        profile_summary=result.get("profile_summary"),
        upgrade_cta=result.get("upgrade_cta", not is_premium),
        upgrade_url="/pricing",
    )


@router.get(
    "/parlay-tips/categories",
    summary="Get tip categories",
    description="Returns available tip categories."
)
async def get_tip_categories():
    """Get list of available tip categories."""
    return {
        "categories": [
            {"id": "bankroll", "name": "Bankroll Management", "icon": "💰"},
            {"id": "strategy", "name": "Strategy", "icon": "🎯"},
            {"id": "value", "name": "Finding Value", "icon": "📈"},
            {"id": "research", "name": "Research", "icon": "🔍"},
            {"id": "timing", "name": "Timing", "icon": "⏰"},
            {"id": "mindset", "name": "Mindset", "icon": "🧘"},
            {"id": "markets", "name": "Markets", "icon": "📊"},
            {"id": "personalized", "name": "Personalized", "icon": "🦍"},
        ]
    }

