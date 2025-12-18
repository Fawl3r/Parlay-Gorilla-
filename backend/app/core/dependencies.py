"""Dependency injection for FastAPI routes"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.database.session import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select

logger = logging.getLogger(__name__)

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
):
    """
    Verify JWT token and return current user
    
    This dependency validates the JWT token and fetches the user
    """
    import uuid
    from app.services.auth_service import decode_access_token
    
    token = credentials.credentials
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    try:
        user_uuid = uuid.UUID(str(user_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Get user from database
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
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


# Aliases for consistency with naming conventions
get_current_user_optional = get_optional_user
get_optional_current_user = get_optional_user
