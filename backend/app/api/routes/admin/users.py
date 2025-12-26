"""
Admin users API routes.

Provides user management:
- List users with filters
- Update user role/plan/status
- Search users
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
import uuid

from app.core.dependencies import get_db
from app.models.user import User, UserRole, UserPlan
from .auth import require_admin

router = APIRouter()


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    username: Optional[str]
    role: str
    plan: str
    is_active: bool
    created_at: str
    last_login: Optional[str]
    
    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    """Request model for updating a user."""
    role: Optional[str] = None
    plan: Optional[str] = None
    is_active: Optional[bool] = None


class UsersListResponse(BaseModel):
    """Paginated users list response."""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("", response_model=UsersListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by email or username"),
    role: Optional[str] = Query(None, description="Filter by role"),
    plan: Optional[str] = Query(None, description="Filter by plan"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List users with pagination and filters.
    """
    query = select(User)
    count_query = select(func.count(User.id))
    
    # Apply filters
    conditions = []
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                User.email.ilike(search_pattern),
                User.username.ilike(search_pattern)
            )
        )
    
    if role:
        conditions.append(User.role == role)
    
    if plan:
        conditions.append(User.plan == plan)
    
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return UsersListResponse(
        users=[
            UserResponse(
                id=str(u.id),
                email=u.email,
                username=u.username,
                role=u.role,
                plan=u.plan,
                is_active=u.is_active,
                created_at=u.created_at.isoformat() if u.created_at else "",
                last_login=u.last_login.isoformat() if u.last_login else None,
            )
            for u in users
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get a single user by ID.
    """
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        role=user.role,
        plan=user.plan,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else "",
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Update a user's role, plan, or active status.
    """
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from demoting themselves
    if str(user.id) == str(admin.id) and update_data.role and update_data.role != UserRole.admin.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself from admin"
        )
    
    # Apply updates
    if update_data.role is not None:
        if update_data.role not in [r.value for r in UserRole]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}"
            )
        user.role = update_data.role
    
    if update_data.plan is not None:
        if update_data.plan not in [p.value for p in UserPlan]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan. Must be one of: {[p.value for p in UserPlan]}"
            )
        user.plan = update_data.plan
    
    if update_data.is_active is not None:
        # Prevent admin from deactivating themselves
        if str(user.id) == str(admin.id) and not update_data.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate yourself"
            )
        user.is_active = update_data.is_active
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        role=user.role,
        plan=user.plan,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else "",
        last_login=user.last_login.isoformat() if user.last_login else None,
    )

