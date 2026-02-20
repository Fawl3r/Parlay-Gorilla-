"""
Admin users API routes. Never returns 500; DB errors return safe fallbacks.
"""

import logging

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import OperationalError, ProgrammingError
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
import uuid

from app.core.dependencies import get_db
from app.core.admin_safe import SAFE_USERS_LIST
from app.models.user import User, UserRole, UserPlan
from .auth import require_admin

logger = logging.getLogger(__name__)

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
    """List users with pagination and filters. Returns safe empty on DB errors."""
    try:
        query = select(User)
        count_query = select(func.count(User.id))
        conditions = []
        if search:
            conditions.append(or_(User.email.ilike(f"%{search}%"), User.username.ilike(f"%{search}%")))
        if role:
            conditions.append(User.role == role)
        if plan:
            conditions.append(User.plan == plan)
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        offset = (page - 1) * page_size
        query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        users = result.scalars().all()
        logger.info("admin.endpoint.success", extra={"endpoint": "users.list"})
        return UsersListResponse(
            users=[
                UserResponse(
                    id=str(u.id),
                    email=u.email or "",
                    username=u.username,
                    role=u.role or "",
                    plan=u.plan or "",
                    is_active=u.is_active,
                    created_at=u.created_at.isoformat() if u.created_at else "",
                    last_login=u.last_login.isoformat() if u.last_login else None,
                )
                for u in users
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=max(0, (total + page_size - 1) // page_size),
        )
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "users.list", "error": str(e)}, exc_info=True)
        return UsersListResponse(**dict(SAFE_USERS_LIST, page=page, page_size=page_size))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get a single user by ID. Returns safe minimal body on DB errors."""
    try:
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        logger.info("admin.endpoint.success", extra={"endpoint": "users.get"})
        return UserResponse(
            id=str(user.id),
            email=user.email or "",
            username=user.username,
            role=user.role or "",
            plan=user.plan or "",
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else "",
            last_login=user.last_login.isoformat() if user.last_login else None,
        )
    except HTTPException:
        raise
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user_id")
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "users.get", "error": str(e)}, exc_info=True)
        return UserResponse(id=user_id, email="", username=None, role="", plan="", is_active=False, created_at="", last_login=None)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Update a user's role, plan, or active status. Never 500."""
    try:
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if str(user.id) == str(admin.id) and update_data.role and update_data.role != UserRole.admin.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot demote yourself from admin")
        if update_data.role is not None:
            if update_data.role not in [r.value for r in UserRole]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}")
            user.role = update_data.role
        if update_data.plan is not None:
            if update_data.plan not in [p.value for p in UserPlan]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid plan. Must be one of: {[p.value for p in UserPlan]}")
            user.plan = update_data.plan
        if update_data.is_active is not None:
            if str(user.id) == str(admin.id) and not update_data.is_active:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself")
            user.is_active = update_data.is_active
        await db.commit()
        await db.refresh(user)
        logger.info("admin.endpoint.success", extra={"endpoint": "users.update"})
        return UserResponse(
            id=str(user.id),
            email=user.email or "",
            username=user.username,
            role=user.role or "",
            plan=user.plan or "",
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else "",
            last_login=user.last_login.isoformat() if user.last_login else None,
        )
    except HTTPException:
        raise
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user_id")
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.exception("admin.endpoint.failure", extra={"endpoint": "users.update"})
        return UserResponse(id=user_id, email="", username=None, role="", plan="", is_active=False, created_at="", last_login=None)

