"""User management API routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

from app.core.dependencies import get_current_user, get_db, get_optional_user
from app.models.user import User
from app.services.auth_service import create_user
from app.services.user_stats_service import UserStatsService

router = APIRouter()


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None


class UserUpgradeRequest(BaseModel):
    premium: bool = True


class UserStatsResponse(BaseModel):
    ai_parlays: dict
    custom_ai_parlays: dict
    inscriptions: dict
    verified_wins: dict
    leaderboards: dict


@router.post("/user/register")
async def register_user(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user
    Note: Prefer `POST /api/auth/register` for the full JWT auth flow.
    """
    try:
        user = await create_user(
            db,
            email=request.email,
            password=request.password,
            username=request.username,
        )
        
        return {
            "message": "User registered successfully",
            "user_id": str(user.id),
            "account_number": user.account_number,
            "email": user.email,
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to register user: {str(e)}")


@router.post("/user/upgrade")
async def upgrade_user(
    request: UserUpgradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_optional_user),
):
    """
    Upgrade/downgrade user premium status
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # NOTE: Subscription/billing is handled elsewhere. This endpoint is a
        # convenience toggle for local/dev tools.
        current_user.plan = "standard" if request.premium else "free"
        await db.commit()
        await db.refresh(current_user)
        
        return {
            "message": f"User {'upgraded' if request.premium else 'downgraded'} successfully",
            "plan": current_user.plan,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.get("/users/me/stats", response_model=UserStatsResponse)
async def get_my_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserStatsService(db)
    return await service.get_user_stats(user)

