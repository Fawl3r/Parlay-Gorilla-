"""Advanced parlay variants routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.core.dependencies import get_db, get_optional_user
from app.models.user import User
from app.services.parlay_variants import ParlayVariantService

router = APIRouter()


class SameGameParlayRequest(BaseModel):
    """Request for same-game parlay"""
    game_id: str
    num_legs: int
    market_types: Optional[list] = None


class RoundRobinRequest(BaseModel):
    """Request for round robin parlay"""
    num_legs: int
    risk_profile: str = "balanced"


class TeaserRequest(BaseModel):
    """Request for teaser parlay"""
    num_legs: int
    points_adjustment: float = 6.0
    risk_profile: str = "balanced"


@router.post("/same-game")
async def create_same_game_parlay(
    request: SameGameParlayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Create a same-game parlay"""
    if request.num_legs < 2 or request.num_legs > 10:
        raise HTTPException(status_code=400, detail="Number of legs must be between 2 and 10")
    
    service = ParlayVariantService(db)
    try:
        parlay = await service.build_same_game_parlay(
            game_id=request.game_id,
            num_legs=request.num_legs,
            market_types=request.market_types
        )
        return parlay
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/round-robin")
async def create_round_robin(
    request: RoundRobinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Create a round robin parlay"""
    if request.num_legs < 3 or request.num_legs > 8:
        raise HTTPException(status_code=400, detail="Number of legs must be between 3 and 8 for round robin")
    
    service = ParlayVariantService(db)
    try:
        round_robin = await service.build_round_robin(
            num_legs=request.num_legs,
            risk_profile=request.risk_profile
        )
        return round_robin
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/teaser")
async def create_teaser(
    request: TeaserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Create a teaser parlay"""
    if request.num_legs < 2 or request.num_legs > 15:
        raise HTTPException(status_code=400, detail="Number of legs must be between 2 and 15")
    
    if request.points_adjustment not in [6.0, 6.5, 10.0]:
        raise HTTPException(status_code=400, detail="Points adjustment must be 6.0, 6.5, or 10.0")
    
    service = ParlayVariantService(db)
    try:
        teaser = await service.build_teaser(
            num_legs=request.num_legs,
            points_adjustment=request.points_adjustment,
            risk_profile=request.risk_profile
        )
        return teaser
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

