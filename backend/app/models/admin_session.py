"""
Admin Session model for admin login tracking.

Tracks admin login sessions for security auditing.
"""

from sqlalchemy import Column, String, DateTime, Index, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class AdminSession(Base):
    """
    Admin session tracking for security auditing.
    
    Records:
    - Admin login events
    - Session duration
    - Access metadata (IP, user agent)
    """
    
    __tablename__ = "admin_sessions"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Admin user reference
    admin_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    admin = relationship("User", back_populates="admin_sessions")
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    
    # Session lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Session status
    is_active = Column(String(10), default="true")  # "true", "false", "expired"
    
    # Indexes
    __table_args__ = (
        Index("idx_admin_sessions_admin_date", "admin_id", "created_at"),
        Index("idx_admin_sessions_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<AdminSession(admin={self.admin_id}, created={self.created_at})>"

