"""Authentication routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from sqlalchemy import select

router = APIRouter()


class UserProfileResponse(BaseModel):
    """User profile response schema"""
    id: str
    email: str
    username: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[str]
    default_risk_profile: str
    favorite_teams: list
    favorite_sports: list
    created_at: str
    last_login: Optional[str]
    
    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """Update user profile request"""
    username: Optional[str] = None
    display_name: Optional[str] = None
    default_risk_profile: Optional[str] = None
    favorite_teams: Optional[list] = None
    favorite_sports: Optional[list] = None


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    user: User = Depends(get_current_user)
):
    """Get current user's profile"""
    return UserProfileResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        default_risk_profile=user.default_risk_profile,
        favorite_teams=user.favorite_teams or [],
        favorite_sports=user.favorite_sports or [],
        created_at=user.created_at.isoformat() if user.created_at else "",
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@router.put("/me", response_model=UserProfileResponse)
async def update_user_profile(
    request: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile"""
    if request.username is not None:
        user.username = request.username
    if request.display_name is not None:
        user.display_name = request.display_name
    if request.default_risk_profile is not None:
        if request.default_risk_profile not in ["conservative", "balanced", "degen"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid risk profile. Must be: conservative, balanced, or degen"
            )
        user.default_risk_profile = request.default_risk_profile
    if request.favorite_teams is not None:
        user.favorite_teams = request.favorite_teams
    if request.favorite_sports is not None:
        user.favorite_sports = request.favorite_sports
    
    await db.commit()
    await db.refresh(user)
    
    return UserProfileResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        default_risk_profile=user.default_risk_profile,
        favorite_teams=user.favorite_teams or [],
        favorite_sports=user.favorite_sports or [],
        created_at=user.created_at.isoformat() if user.created_at else "",
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a user's public profile (if allowed)"""
    # For now, only allow users to see their own profile
    # In the future, can add public profile settings
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    return UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        default_risk_profile=current_user.default_risk_profile,
        favorite_teams=current_user.favorite_teams or [],
        favorite_sports=current_user.favorite_sports or [],
        created_at=current_user.created_at.isoformat() if current_user.created_at else "",
        last_login=current_user.last_login.isoformat() if current_user.last_login else None,
    )

