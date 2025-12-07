"""
Profile API routes for user profile management.

Endpoints:
- GET /api/profile/me - Get profile with stats and badges
- PUT /api/profile/me - Update profile
- POST /api/profile/setup - Complete initial profile setup
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.profile_service import ProfileService
from app.services.badge_service import BadgeService

router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================

class ProfileUpdateRequest(BaseModel):
    """Schema for profile update requests."""
    display_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = Field(None, max_length=50)
    default_risk_profile: Optional[str] = Field(None, pattern="^(conservative|balanced|degen)$")
    favorite_teams: Optional[List[str]] = None
    favorite_sports: Optional[List[str]] = None


class ProfileSetupRequest(BaseModel):
    """Schema for profile setup requests."""
    display_name: str = Field(..., min_length=1, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = Field(None, max_length=50)
    default_risk_profile: Optional[str] = Field("balanced", pattern="^(conservative|balanced|degen)$")
    favorite_teams: Optional[List[str]] = Field(default_factory=list)
    favorite_sports: Optional[List[str]] = Field(default_factory=list)


class UserResponse(BaseModel):
    """Schema for user data in responses."""
    id: str
    email: str
    username: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    timezone: Optional[str]
    email_verified: bool
    profile_completed: bool
    default_risk_profile: str
    favorite_teams: List[str]
    favorite_sports: List[str]
    role: str
    plan: str
    created_at: Optional[str]
    last_login: Optional[str]


class ParlayStatsResponse(BaseModel):
    """Schema for parlay statistics."""
    total_parlays: int
    by_sport: Dict[str, int]
    by_risk_profile: Dict[str, int]


class BadgeResponse(BaseModel):
    """Schema for badge data."""
    id: str
    name: str
    slug: str
    description: Optional[str]
    icon: Optional[str]
    requirement_type: str
    requirement_value: int
    display_order: int
    unlocked: bool
    unlocked_at: Optional[str]


class ProfileResponse(BaseModel):
    """Schema for full profile response."""
    user: UserResponse
    stats: ParlayStatsResponse
    badges: List[BadgeResponse]


# ============================================================================
# Profile Endpoints
# ============================================================================

@router.get("/profile/me", response_model=ProfileResponse)
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's full profile.
    
    Returns:
    - User profile data
    - Parlay statistics
    - All badges with unlock status
    """
    profile_service = ProfileService(db)
    profile = await profile_service.get_profile(str(user.id))
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return ProfileResponse(
        user=UserResponse(**profile["user"]),
        stats=ParlayStatsResponse(**profile["stats"]),
        badges=[BadgeResponse(**b) for b in profile["badges"]],
    )


@router.put("/profile/me", response_model=UserResponse)
async def update_my_profile(
    request: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user's profile.
    
    Allowed fields:
    - display_name
    - avatar_url
    - bio
    - timezone
    - default_risk_profile
    - favorite_teams
    - favorite_sports
    """
    profile_service = ProfileService(db)
    
    # Only include non-None values
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated_user = await profile_service.update_profile(str(user.id), update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**updated_user)


@router.post("/profile/setup", response_model=UserResponse)
async def complete_profile_setup(
    request: ProfileSetupRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete initial profile setup.
    
    This endpoint:
    1. Updates profile fields
    2. Sets profile_completed = True
    3. Awards "Complete Profile" badge if available
    
    Required: display_name
    """
    profile_service = ProfileService(db)
    badge_service = BadgeService(db)
    
    try:
        updated_user = await profile_service.complete_profile_setup(
            str(user.id),
            request.model_dump()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Award profile completion badge
    await badge_service.award_badge_by_slug(str(user.id), "profile-complete")
    
    return UserResponse(**updated_user)


@router.get("/profile/badges", response_model=List[BadgeResponse])
async def get_my_badges(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all badges with unlock status for current user.
    
    Returns all badges, each with:
    - Badge info (name, description, icon, requirement)
    - unlocked: boolean
    - unlocked_at: timestamp if unlocked
    """
    badge_service = BadgeService(db)
    badges = await badge_service.get_user_badges(str(user.id))
    
    return [BadgeResponse(**b) for b in badges]

