"""
Admin authentication dependency.

Provides role-based access control for admin routes.
Supports email/password and allowlisted Solana wallet (Phantom) login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user
from app.models.user import User, UserRole
from app.services.auth_service import authenticate_user, create_access_token

router = APIRouter()

# Fallback allowlisted admin wallet (Phantom) when env not set
_DEFAULT_ADMIN_WALLET = "4E58m1qpnxbFRoDZ8kk9zu3GT6YLrPtPk65u8Xa2ZgBU"


def _get_allowed_wallets() -> set[str]:
    raw = (settings.admin_wallet_addresses or "").strip()
    if not raw:
        return {_DEFAULT_ADMIN_WALLET}
    return {a.strip() for a in raw.split(",") if a.strip()}


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminWalletLoginRequest(BaseModel):
    wallet_address: str


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


@router.post("/login-wallet", response_model=AdminLoginResponse)
async def admin_login_wallet(
    request: AdminWalletLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate an admin using an allowlisted Solana wallet address (e.g. Phantom).

    The wallet must be in ADMIN_WALLET_ADDRESSES (or the default allowlist).
    Issues a JWT for an existing admin user so /api/auth/me and require_admin work unchanged.
    """
    address = (request.wallet_address or "").strip()
    if not address:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="wallet_address required")

    allowed = _get_allowed_wallets()
    if address not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wallet not authorized for admin access")

    result = await db.execute(
        select(User).where(User.role == UserRole.admin.value).limit(1)
    )
    admin_user = result.scalar_one_or_none()
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No admin user configured. Create a user with role=admin for email/password or wallet login.",
        )

    token = create_access_token(
        {"sub": str(admin_user.id), "email": admin_user.email, "role": admin_user.role}
    )
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

