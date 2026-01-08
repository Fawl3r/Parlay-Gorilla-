"""
Admin authentication dependency.

Provides role-based access control for admin routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.core.dependencies import get_db, get_current_user
from app.models.user import User, UserRole
from app.services.auth_service import authenticate_user, create_access_token

router = APIRouter()

class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    detail: Optional[str] = None


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    request: AdminLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate an admin using email/password.

    This is admin-only access. It does not create users.
    """
    user = await authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.role != UserRole.admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return AdminLoginResponse(success=True, token=token, detail="Admin authentication successful")


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that requires the current user to have admin role.
    
    Raises:
        HTTPException 403: If user is not an admin
    
    Returns:
        The authenticated admin user
    """
    if current_user.role != UserRole.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


async def require_mod_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that requires the current user to have mod or admin role.
    
    Raises:
        HTTPException 403: If user is not a mod or admin
    
    Returns:
        The authenticated user
    """
    if current_user.role not in (UserRole.mod.value, UserRole.admin.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator or admin access required"
        )
    
    return current_user

