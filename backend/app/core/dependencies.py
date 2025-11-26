"""Dependency injection for FastAPI routes"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from typing import Annotated
import httpx

from app.database.session import AsyncSessionLocal
from app.core.config import settings
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.sql import func

security = HTTPBearer()

class OptionalHTTPBearer(HTTPBearer):
    """HTTPBearer that doesn't raise error when token is missing"""
    async def __call__(self, request=None):
        try:
            if request is None:
                return None
            if not hasattr(request, 'headers') or request.headers is None:
                return None
            return await super().__call__(request)
        except HTTPException:
            return None
        except Exception as e:
            # Handle any other errors (like NoneType errors)
            print(f"Error in OptionalHTTPBearer: {e}")
            return None

optional_security = OptionalHTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Verify JWT token from Supabase and return current user
    
    This dependency validates the JWT token and fetches/creates the user
    """
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication not configured"
        )
    
    token = credentials.credentials
    
    # Verify token with Supabase
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": settings.supabase_anon_key
                },
                timeout=5.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token"
                )
            
            supabase_user = response.json()
            supabase_user_id = supabase_user.get("id")
            email = supabase_user.get("email")
            
            if not supabase_user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user data"
                )
            
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
    
    # Get or create user in our database
    result = await db.execute(
        select(User).where(User.supabase_user_id == supabase_user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(
            supabase_user_id=supabase_user_id,
            email=email or "",
            username=supabase_user.get("user_metadata", {}).get("username"),
            display_name=supabase_user.get("user_metadata", {}).get("display_name"),
            avatar_url=supabase_user.get("user_metadata", {}).get("avatar_url"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update last login
        from datetime import datetime, timezone
        user.last_login = datetime.now(timezone.utc)
        await db.commit()
    
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
