"""
API Routes for Live Games, Live Insights, and Real-time Updates.

Endpoints:
- GET /api/live-games - List all live/recent games
- GET /api/live-games/{game_id} - Get specific game with drives
- GET /api/live-insights/{game_id} - Get AI insights (PREMIUM ONLY)
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database.session import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.services.live_game_service import LiveGameService
from app.services.live_insights_service import LiveInsightsService
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/api", tags=["live-games"])


# ============= Response Models =============

class DriveResponse(BaseModel):
    """Response model for a single drive."""
    id: str
    drive_number: int
    team: str
    quarter: Optional[int] = None
    result: Optional[str] = None
    points_scored: int = 0
    description: Optional[str] = None
    home_score_after: Optional[int] = None
    away_score_after: Optional[int] = None

    class Config:
        from_attributes = True


class LiveGameResponse(BaseModel):
    """Response model for live game data."""
    id: str
    external_game_id: str
    sport: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    status: str
    quarter: Optional[int] = None
    period_name: Optional[str] = None
    time_remaining: Optional[str] = None
    scheduled_start: Optional[str] = None
    last_updated_at: Optional[str] = None
    drives: List[DriveResponse] = []

    class Config:
        from_attributes = True


class LiveGamesListResponse(BaseModel):
    """Response model for list of live games."""
    games: List[LiveGameResponse]
    count: int
    sport: Optional[str] = None


class LiveInsightsResponse(BaseModel):
    """Response model for AI live insights."""
    game_id: str
    matchup: str
    score: str
    status: str
    period: Optional[str] = None
    time_remaining: Optional[str] = None
    insights: dict
    generated_at: Optional[str] = None


class UpgradeRequiredResponse(BaseModel):
    """Response when premium feature is accessed by free user."""
    error: str = "upgrade_required"
    message: str = "This feature requires a Premium subscription."
    upgrade_url: str = "/pricing"


# ============= Endpoints =============

@router.get(
    "/live-games",
    response_model=LiveGamesListResponse,
    summary="Get all live games",
    description="Returns all games that are currently in progress or recently finished."
)
async def get_live_games(
    sport: Optional[str] = Query(None, description="Filter by sport (nfl, nba, nhl, mlb)"),
    include_finals: bool = Query(True, description="Include recently finished games"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all live and recently finished games.
    
    - **sport**: Optional filter by sport type
    - **include_finals**: Whether to include games that ended in last 2 hours
    """
    service = LiveGameService(db)
    games = await service.get_all_live_games(sport=sport, include_recent_finals=include_finals)
    
    # Convert to response format
    games_response = []
    for game in games:
        games_response.append(LiveGameResponse(
            id=str(game.id),
            external_game_id=game.external_game_id,
            sport=game.sport,
            home_team=game.home_team,
            away_team=game.away_team,
            home_score=game.home_score,
            away_score=game.away_score,
            status=game.status,
            quarter=game.quarter,
            period_name=game.period_name,
            time_remaining=game.time_remaining,
            scheduled_start=game.scheduled_start.isoformat() if game.scheduled_start else None,
            last_updated_at=game.last_updated_at.isoformat() if game.last_updated_at else None,
            drives=[],  # Don't include drives in list view
        ))
    
    return LiveGamesListResponse(
        games=games_response,
        count=len(games_response),
        sport=sport,
    )


@router.get(
    "/live-games/{game_id}",
    response_model=LiveGameResponse,
    summary="Get live game details",
    description="Returns detailed live game data including all drives/possessions."
)
async def get_live_game(
    game_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed live game data with drives.
    
    - **game_id**: Internal game UUID
    """
    service = LiveGameService(db)
    game_data = await service.get_live_game_with_drives(game_id)
    
    if not game_data:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Convert drives
    drives = [
        DriveResponse(**drive_data)
        for drive_data in game_data.get("drives", [])
    ]
    
    return LiveGameResponse(
        id=game_data["id"],
        external_game_id=game_data["external_game_id"],
        sport=game_data["sport"],
        home_team=game_data["home_team"],
        away_team=game_data["away_team"],
        home_score=game_data["home_score"],
        away_score=game_data["away_score"],
        status=game_data["status"],
        quarter=game_data.get("quarter"),
        period_name=game_data.get("period_name"),
        time_remaining=game_data.get("time_remaining"),
        scheduled_start=game_data.get("scheduled_start"),
        last_updated_at=game_data.get("last_updated_at"),
        drives=drives,
    )


@router.get(
    "/live-insights/{game_id}",
    responses={
        200: {"model": LiveInsightsResponse},
        403: {"model": UpgradeRequiredResponse},
        404: {"description": "Game not found"},
    },
    summary="Get AI live insights (Premium)",
    description="Returns AI-generated real-time analysis for a live game. Premium users only."
)
async def get_live_insights(
    game_id: str,
    include_betting: bool = Query(True, description="Include betting angle analysis"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI-powered live insights for a game.
    
    **PREMIUM FEATURE** - Free users will receive upgrade prompt.
    
    - **game_id**: Internal game UUID
    - **include_betting**: Include betting strategy analysis
    """
    # Check if user is premium
    subscription_service = SubscriptionService(db)
    is_premium = await subscription_service.is_user_premium(str(user.id))
    
    if not is_premium:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "upgrade_required",
                "message": "AI Live Insights is a Premium feature. Upgrade to access real-time game analysis.",
                "upgrade_url": "/pricing",
            }
        )
    
    # Generate insights
    insights_service = LiveInsightsService(db)
    insights = await insights_service.generate_live_insights(
        game_id,
        include_betting_angles=include_betting
    )
    
    if "error" in insights and insights.get("error") == "Game not found":
        raise HTTPException(status_code=404, detail="Game not found")
    
    return LiveInsightsResponse(
        game_id=insights.get("game_id", game_id),
        matchup=insights.get("matchup", ""),
        score=insights.get("score", "0 - 0"),
        status=insights.get("status", "unknown"),
        period=insights.get("period"),
        time_remaining=insights.get("time_remaining"),
        insights=insights.get("insights", {}),
        generated_at=insights.get("generated_at"),
    )


@router.get(
    "/live-insights/{game_id}/preview",
    summary="Preview live insights (limited)",
    description="Returns limited preview of insights for free users."
)
async def get_live_insights_preview(
    game_id: str,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a preview of live insights (limited for non-premium users).
    
    Shows truncated insights with upgrade CTA.
    """
    insights_service = LiveInsightsService(db)
    insights = await insights_service.generate_live_insights(game_id, include_betting_angles=False)
    
    if "error" in insights and insights.get("error") == "Game not found":
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Check if premium for full access
    is_premium = False
    if user:
        subscription_service = SubscriptionService(db)
        is_premium = await subscription_service.is_user_premium(str(user.id))
    
    if is_premium:
        # Return full insights
        return insights
    
    # Return limited preview
    full_insights = insights.get("insights", {})
    preview_insights = {
        "momentum": full_insights.get("momentum", "Upgrade to Premium for live momentum analysis."),
        "key_factors": "🔒 Premium Feature - Upgrade to see key factors analysis.",
        "probability_shift": "🔒 Premium Feature - Upgrade to see probability shifts.",
        "matchup_analysis": "🔒 Premium Feature - Upgrade for full matchup analysis.",
    }
    
    return {
        **insights,
        "insights": preview_insights,
        "is_preview": True,
        "upgrade_message": "Upgrade to Premium for full AI insights, betting angles, and more!",
        "upgrade_url": "/pricing",
    }

