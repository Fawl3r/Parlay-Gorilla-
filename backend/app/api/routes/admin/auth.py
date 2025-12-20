"""
Admin authentication dependency.

Provides role-based access control for admin routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from jose import jwt
from datetime import datetime, timedelta

from app.core.dependencies import get_db, get_current_user
from app.core.config import settings
from app.models.user import User, UserRole, UserPlan
from app.services.accounts.account_number_service import AccountNumberAllocator

router = APIRouter()

# Authorized admin wallet address
ADMIN_WALLET_ADDRESS = "4E58m1qpnxbFRoDZ8kk9zu3GT6YLrPtPk65u8Xa2ZgBU"


class WalletLoginRequest(BaseModel):
    """Wallet login request model."""
    wallet_address: str
    message: Optional[str] = None


class WalletLoginResponse(BaseModel):
    """Wallet login response model."""
    success: bool
    token: Optional[str] = None
    detail: Optional[str] = None


@router.post("/wallet-login", response_model=WalletLoginResponse)
async def wallet_login(
    request: WalletLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate admin using Solana wallet address.
    
    Only the authorized wallet address can access the admin dashboard.
    """
    wallet_address = request.wallet_address.strip()
    
    # Verify wallet address matches authorized admin address
    if wallet_address != ADMIN_WALLET_ADDRESS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Wallet address {wallet_address[:8]}... is not authorized for admin access."
        )
    
    # Find or create admin user with this wallet address
    from sqlalchemy import select
    
    # Check if user exists with this wallet address
    result = await db.execute(
        select(User).where(User.email == f"admin_{wallet_address[:8]}@parlaygorilla.com")
    )
    admin_user = result.scalar_one_or_none()
    
    if not admin_user:
        # Create admin user if it doesn't exist
        import uuid
        allocator = AccountNumberAllocator()
        admin_user = User(
            id=uuid.uuid4(),
            email=f"admin_{wallet_address[:8]}@parlaygorilla.com",
            account_number=await allocator.allocate(db),
            username=f"admin_{wallet_address[:8]}",
            role=UserRole.admin.value,
            plan=UserPlan.elite.value,
            is_active=True,
        )
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
    
    # Ensure user has admin role
    if admin_user.role != UserRole.admin.value:
        admin_user.role = UserRole.admin.value
        await db.commit()
        await db.refresh(admin_user)
    
    # Generate JWT token for admin session
    token_data = {
        "sub": str(admin_user.id),
        "email": admin_user.email,
        "role": admin_user.role,  # role is already stored as string value in DB
        "wallet_address": wallet_address,
        "exp": datetime.utcnow() + timedelta(days=7),  # 7 day expiry
    }
    
    # Use the same secret key as regular auth
    secret_key = settings.jwt_secret
    token = jwt.encode(token_data, secret_key, algorithm="HS256")
    
    return WalletLoginResponse(
        success=True,
        token=token,
        detail="Admin authentication successful"
    )


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

