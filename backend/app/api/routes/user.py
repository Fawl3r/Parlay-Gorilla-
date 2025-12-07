"""User management API routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

from app.core.dependencies import get_db, get_optional_user
from app.models.user import User

router = APIRouter()


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None


class UserUpgradeRequest(BaseModel):
    premium: bool = True


@router.post("/user/register")
async def register_user(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user
    Note: This is a basic registration. For production, use Supabase Auth.
    """
    try:
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == request.email)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create new user
        # In production, this would integrate with Supabase Auth
        user = User(
            id=uuid.uuid4(),
            supabase_user_id=f"local_{uuid.uuid4()}",  # Placeholder
            email=request.email,
            username=request.username,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return {
            "message": "User registered successfully",
            "user_id": str(user.id),
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
        # In production, this would check payment status
        current_user.premium = request.premium
        await db.commit()
        await db.refresh(current_user)
        
        return {
            "message": f"User {'upgraded' if request.premium else 'downgraded'} successfully",
            "premium": current_user.premium,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

