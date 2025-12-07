"""
Verification Service for email verification and password reset.

Provides:
- Secure token generation (cryptographically secure, hashed storage)
- Token verification
- Email verification flow
- Password reset flow
- Token cleanup
"""

from typing import Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
import uuid
import logging

from app.models.user import User
from app.models.verification_token import VerificationToken, TokenType
from app.services.auth_service import get_password_hash

logger = logging.getLogger(__name__)


# Token expiration times
EMAIL_VERIFY_EXPIRE_HOURS = 48  # 2 days for email verification
PASSWORD_RESET_EXPIRE_HOURS = 2  # 2 hours for password reset


class VerificationService:
    """
    Service for verification token operations.
    
    Security:
    - Tokens are cryptographically secure (secrets.token_hex)
    - Only SHA-256 hash is stored in DB
    - Tokens are single-use (marked as used after verification)
    - Tokens have expiration times
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_email_verification_token(
        self, 
        user_id: str
    ) -> Tuple[VerificationToken, str]:
        """
        Create an email verification token for a user.
        
        Returns:
            Tuple of (VerificationToken, raw_token)
            raw_token should be included in verification URL
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            raise ValueError(f"Invalid user_id: {user_id}")
        
        # Invalidate any existing unused tokens for this user/type
        await self._invalidate_existing_tokens(user_uuid, TokenType.EMAIL_VERIFY)
        
        # Create new token
        token, raw_token = VerificationToken.create_token(
            user_id=user_uuid,
            token_type=TokenType.EMAIL_VERIFY,
            expires_in_hours=EMAIL_VERIFY_EXPIRE_HOURS,
        )
        
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        
        logger.info(f"Created email verification token for user {user_id}")
        
        return token, raw_token
    
    async def create_password_reset_token(
        self, 
        user_id: str
    ) -> Tuple[VerificationToken, str]:
        """
        Create a password reset token for a user.
        
        Returns:
            Tuple of (VerificationToken, raw_token)
            raw_token should be included in reset URL
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            raise ValueError(f"Invalid user_id: {user_id}")
        
        # Invalidate any existing unused tokens for this user/type
        await self._invalidate_existing_tokens(user_uuid, TokenType.PASSWORD_RESET)
        
        # Create new token
        token, raw_token = VerificationToken.create_token(
            user_id=user_uuid,
            token_type=TokenType.PASSWORD_RESET,
            expires_in_hours=PASSWORD_RESET_EXPIRE_HOURS,
        )
        
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        
        logger.info(f"Created password reset token for user {user_id}")
        
        return token, raw_token
    
    async def verify_email_token(self, raw_token: str) -> Optional[User]:
        """
        Verify an email verification token.
        
        If valid:
        - Marks token as used
        - Sets user.email_verified = True
        - Returns the user
        
        If invalid/expired/used:
        - Returns None
        """
        token = await self._verify_token(raw_token, TokenType.EMAIL_VERIFY)
        
        if not token:
            return None
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == token.user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Mark user as verified
        user.email_verified = True
        
        # Mark token as used
        token.mark_used()
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"Email verified for user {user.id}")
        
        return user
    
    async def verify_password_reset_token(self, raw_token: str) -> Optional[User]:
        """
        Verify a password reset token.
        
        If valid:
        - Returns the user (token NOT marked as used yet - call reset_password to complete)
        
        If invalid/expired/used:
        - Returns None
        """
        token = await self._verify_token(raw_token, TokenType.PASSWORD_RESET)
        
        if not token:
            return None
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == token.user_id)
        )
        user = result.scalar_one_or_none()
        
        return user
    
    async def reset_password(self, raw_token: str, new_password: str) -> Optional[User]:
        """
        Reset a user's password using a reset token.
        
        If valid:
        - Updates user's password hash
        - Marks token as used
        - Returns the user
        
        If invalid/expired/used:
        - Returns None
        """
        token = await self._verify_token(raw_token, TokenType.PASSWORD_RESET)
        
        if not token:
            return None
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == token.user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        
        # Mark token as used
        token.mark_used()
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"Password reset for user {user.id}")
        
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email for password reset request."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def cleanup_expired_tokens(self) -> int:
        """
        Delete all expired tokens.
        
        Should be called periodically (e.g., daily) to clean up DB.
        
        Returns number of deleted tokens.
        """
        now = datetime.now(timezone.utc)
        
        result = await self.db.execute(
            delete(VerificationToken).where(
                VerificationToken.expires_at < now
            )
        )
        
        await self.db.commit()
        
        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired verification tokens")
        
        return deleted_count
    
    async def _verify_token(
        self, 
        raw_token: str, 
        token_type: str
    ) -> Optional[VerificationToken]:
        """
        Internal method to verify a token.
        
        Returns the token if valid, None otherwise.
        """
        # Hash the incoming token
        token_hash = VerificationToken.hash_token(raw_token)
        
        # Find token by hash
        result = await self.db.execute(
            select(VerificationToken).where(
                and_(
                    VerificationToken.token_hash == token_hash,
                    VerificationToken.token_type == token_type,
                )
            )
        )
        token = result.scalar_one_or_none()
        
        if not token:
            logger.debug(f"Token not found for type {token_type}")
            return None
        
        # Check if valid
        if not token.is_valid:
            if token.is_expired:
                logger.debug(f"Token expired for type {token_type}")
            elif token.is_used:
                logger.debug(f"Token already used for type {token_type}")
            return None
        
        return token
    
    async def _invalidate_existing_tokens(
        self, 
        user_id: uuid.UUID, 
        token_type: str
    ) -> None:
        """
        Invalidate any existing unused tokens for a user/type.
        
        This prevents multiple valid tokens existing simultaneously.
        """
        # Delete unused tokens for this user/type
        await self.db.execute(
            delete(VerificationToken).where(
                and_(
                    VerificationToken.user_id == user_id,
                    VerificationToken.token_type == token_type,
                    VerificationToken.used_at.is_(None),
                )
            )
        )


# Helper function for dependency injection
async def get_verification_service(db: AsyncSession) -> VerificationService:
    """Get verification service instance."""
    return VerificationService(db)

