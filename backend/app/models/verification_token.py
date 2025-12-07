"""
Verification Token model for email verification and password reset.

Security considerations:
- Stores SHA-256 hash of token, never raw token
- Index on expires_at for fast cleanup queries
- Tokens are single-use (marked used_at after verification)
"""

from sqlalchemy import Column, String, DateTime, Index, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Tuple

from app.database.session import Base
from app.database.types import GUID


class TokenType:
    """Token type constants"""
    EMAIL_VERIFY = "email_verify"
    PASSWORD_RESET = "password_reset"


class VerificationToken(Base):
    """
    Secure verification tokens for email verification and password reset.
    
    Security:
    - Raw token is returned to user (for URL), hash is stored in DB
    - SHA-256 hashing prevents token exposure if DB is compromised
    - Expiration prevents indefinite token validity
    - Single-use: marked as used after successful verification
    """
    
    __tablename__ = "verification_tokens"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # User reference
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Token storage (SHA-256 hash, 64 hex characters)
    token_hash = Column(String(64), nullable=False, index=True)
    
    # Token type
    token_type = Column(String(20), nullable=False, index=True)
    
    # Expiration and usage tracking
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_verification_token_hash", "token_hash"),
        Index("idx_verification_token_expires", "expires_at"),
        Index("idx_verification_token_user_type", "user_id", "token_type"),
    )
    
    def __repr__(self):
        return f"<VerificationToken(id={self.id}, type={self.token_type}, expires={self.expires_at})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if token has expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_used(self) -> bool:
        """Check if token has been used"""
        return self.used_at is not None
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)"""
        return not self.is_expired and not self.is_used
    
    def mark_used(self) -> None:
        """Mark token as used"""
        self.used_at = datetime.now(timezone.utc)
    
    @staticmethod
    def hash_token(raw_token: str) -> str:
        """Hash a raw token using SHA-256"""
        return hashlib.sha256(raw_token.encode()).hexdigest()
    
    @staticmethod
    def generate_token() -> str:
        """Generate a cryptographically secure random token"""
        return secrets.token_hex(32)  # 64 character hex string
    
    @classmethod
    def create_token(
        cls,
        user_id: uuid.UUID,
        token_type: str,
        expires_in_hours: int = 24
    ) -> Tuple["VerificationToken", str]:
        """
        Create a new verification token.
        
        Returns:
            Tuple of (VerificationToken instance, raw_token string)
            
        The raw_token should be sent to user (in URL), 
        while the VerificationToken has the hash stored.
        """
        raw_token = cls.generate_token()
        token_hash = cls.hash_token(raw_token)
        
        token = cls(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            token_type=token_type,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
        )
        
        return token, raw_token

