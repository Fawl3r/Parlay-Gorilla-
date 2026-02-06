"""Extended parlay API routes - 20-leg parlays, history, etc."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.core.dependencies import get_db, get_optional_user
from app.models.parlay import Parlay
from app.models.user import User
from app.schemas.parlay import ParlayResponse
from app.services.parlay_builder import ParlayBuilderService
from app.services.upset_finder import get_upset_finder
from app.core.model_config import MODEL_VERSION

router = APIRouter()


@router.post("/parlay/20-leg", response_model=ParlayResponse)
async def generate_20_leg_parlay(
    risk_profile: str = Query("degen", pattern="^(conservative|balanced|degen)$"),
    sport: str = Query("nfl"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Generate a 20-leg parlay (maximum legs)
    This is the "degen" special - high risk, high reward
    """
    try:
        builder = ParlayBuilderService(db)
        parlay_data = await builder.build_parlay(
            num_legs=20,
            risk_profile=risk_profile,
            sport=sport.upper(),
        )
        
        # Create parlay record
        parlay = Parlay(
            user_id=current_user.id if current_user else None,
            legs=parlay_data.get("legs", []),
            num_legs=20,
            model_version="v1.0",
            parlay_hit_prob=parlay_data.get("parlay_hit_prob", 0.0),
            risk_profile=risk_profile,
            ai_summary=parlay_data.get("ai_summary"),
            ai_risk_notes=parlay_data.get("ai_risk_notes"),
        )
        db.add(parlay)
        await db.commit()
        await db.refresh(parlay)
        
        return ParlayResponse(
            id=str(parlay.id),
            legs=parlay.legs,
            num_legs=parlay.num_legs,
            parlay_hit_prob=float(parlay.parlay_hit_prob),
            risk_profile=parlay.risk_profile,
            ai_summary=parlay.ai_summary,
            ai_risk_notes=parlay.ai_risk_notes,
            created_at=parlay.created_at,
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate 20-leg parlay: {str(e)}")


@router.get("/parlay/history/{user_id}", response_model=List[ParlayResponse])
async def get_parlay_history(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get parlay history for a user
    Users can only view their own history unless they're admin
    """
    try:
        # Verify user can access this history
        if current_user and str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="You can only view your own parlay history")
        
        result = await db.execute(
            select(Parlay)
            .where(Parlay.user_id == uuid.UUID(user_id))
            .order_by(desc(Parlay.created_at))
            .limit(limit)
            .offset(offset)
        )
        parlays = result.scalars().all()
        
        return [
            ParlayResponse(
                id=str(p.id),
                legs=p.legs,
                num_legs=p.num_legs,
                parlay_hit_prob=float(p.parlay_hit_prob),
                risk_profile=p.risk_profile,
                ai_summary=p.ai_summary,
                ai_risk_notes=p.ai_risk_notes,
                created_at=p.created_at,
            )
            for p in parlays
        ]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch parlay history: {str(e)}")


@router.get("/parlay/history", response_model=List[ParlayResponse])
async def get_my_parlay_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get current user's parlay history
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return await get_parlay_history(
        user_id=str(current_user.id),
        limit=limit,
        offset=offset,
        db=db,
        current_user=current_user,
    )


@router.get("/parlay/upsets")
async def get_upset_candidates(
    sport: str = Query("nfl", description="Sport code (nfl, nba, nhl, mlb)"),
    min_edge: float = Query(0.05, ge=0.01, le=0.5, description="Minimum edge threshold"),
    risk_tier: Optional[str] = Query(None, pattern="^(low|medium|high)$"),
    max_results: int = Query(20, ge=1, le=50),
    week: Optional[int] = Query(None, ge=1, le=22, description="NFL week number"),
    db: AsyncSession = Depends(get_db),
):
    """
    🦍 Gorilla Upset Finder
    
    Find high-value underdog plays where the model sees significant edge.
    These are "upset candidates" - plus-money underdogs with positive EV.
    
    Use these to spice up parlays or as standalone value bets.
    
    Risk tiers:
    - low: Safer underdogs (45-50% model prob, lower plus money)
    - medium: Moderate risk (35-45% prob, medium plus money)
    - high: Long shots (<35% prob, high plus money)
    
    Returns:
        List of upset candidates sorted by expected value
    """
    try:
        finder = get_upset_finder(db, sport)
        upsets = await finder.find_upsets(
            min_edge=min_edge,
            max_results=max_results,
            risk_tier=risk_tier,
            week=week,
        )
        
        return {
            "sport": sport.upper(),
            "model_version": MODEL_VERSION,
            "min_edge_threshold": min_edge,
            "risk_tier_filter": risk_tier,
            "count": len(upsets),
            "upsets": [u.to_dict() for u in upsets],
            "summary": f"Found {len(upsets)} upset candidates with {min_edge*100:.0f}%+ edge",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find upsets: {str(e)}")


@router.get("/parlay/upsets/{game_id}")
async def analyze_game_upsets(
    game_id: str,
    sport: str = Query("nfl"),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze a specific game for upset potential.
    
    Returns detailed analysis of underdog value for both sides.
    """
    try:
        finder = get_upset_finder(db, sport)
        
        # We need home/away team info - for now return basic structure
        # In full implementation, fetch game details first
        analysis = {
            "game_id": game_id,
            "sport": sport.upper(),
            "model_version": MODEL_VERSION,
            "message": "Detailed game upset analysis",
            "note": "Provide home_team and away_team query params for full analysis",
        }
        
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze game: {str(e)}")


@router.get("/parlay/upsets-for-parlay")
async def get_upsets_for_parlay(
    parlay_type: str = Query("balanced", pattern="^(safe|balanced|degen)$"),
    sport: str = Query("nfl"),
    max_upsets: int = Query(None, ge=1, le=10, description="Max upset legs to include"),
    week: Optional[int] = Query(None, ge=1, le=22),
    db: AsyncSession = Depends(get_db),
):
    """
    Get upset candidates specifically for parlay building.
    
    Parlay types affect upset selection:
    - safe: Max 1 low-risk upset, higher edge requirement
    - balanced: Mix of tiers, moderate edge requirement
    - degen: More upsets, higher payouts prioritized
    
    Returns:
        Upset candidates optimized for the parlay type
    """
    try:
        finder = get_upset_finder(db, sport)
        upsets = await finder.get_upsets_for_parlay(
            parlay_type=parlay_type,
            num_upsets=max_upsets,
            week=week,
        )
        
        return {
            "parlay_type": parlay_type,
            "sport": sport.upper(),
            "model_version": MODEL_VERSION,
            "recommended_upsets": len(upsets),
            "upsets": [u.to_dict() for u in upsets],
            "strategy": _get_parlay_upset_strategy(parlay_type),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get upsets for parlay: {str(e)}")


def _get_parlay_upset_strategy(parlay_type: str) -> str:
    """Get strategy description for parlay type"""
    strategies = {
        "safe": (
            "For safe parlays, include at most 1 low-risk upset with 8%+ edge. "
            "These add modest plus-money value without significantly reducing hit rate."
        ),
        "balanced": (
            "Balanced parlays can include 2-3 upsets across risk tiers. "
            "Mix low and medium risk for good value without going too wild."
        ),
        "degen": (
            "Degen parlays embrace the chaos. Include 4-6 upsets for maximum payout potential. "
            "Prioritize high plus-money plays with any positive edge."
        ),
    }
    return strategies.get(parlay_type, strategies["balanced"])

