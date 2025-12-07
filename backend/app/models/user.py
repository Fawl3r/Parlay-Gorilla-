"""User model for authentication and profiles"""

from sqlalchemy import Column, String, DateTime, Index, JSON, Boolean, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database.session import Base
from app.database.types import GUID


class UserRole(str, enum.Enum):
    """User role enumeration"""
    user = "user"
    mod = "mod"
    admin = "admin"


class UserPlan(str, enum.Enum):
    """User subscription plan enumeration"""
    free = "free"
    standard = "standard"
    elite = "elite"


class User(Base):
    """User model for storing user profiles and preferences"""
    
    __tablename__ = "users"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    supabase_user_id = Column(String, unique=True, nullable=True, index=True)  # Optional, for migration (can be removed later)
    email = Column(String, nullable=False, unique=True, index=True)
    username = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)  # For JWT-based auth
    
    # Role and access control
    role = Column(String, default=UserRole.user.value, nullable=False)
    plan = Column(String, default=UserPlan.free.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Email verification and profile completion status
    email_verified = Column(Boolean, default=False, nullable=False)
    profile_completed = Column(Boolean, default=False, nullable=False)
    
    # User preferences
    default_risk_profile = Column(String, default="balanced")  # conservative, balanced, degen
    favorite_teams = Column(JSON, default=list)  # List of favorite team names
    favorite_sports = Column(JSON, default=list)  # List of favorite sports
    
    # Profile
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)  # User bio/description
    timezone = Column(String(50), nullable=True)  # User's timezone (e.g., "America/New_York")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    parlays = relationship("Parlay", back_populates="user", lazy="dynamic")
    payments = relationship("Payment", back_populates="user", lazy="dynamic")
    subscriptions = relationship("Subscription", back_populates="user", lazy="dynamic")
    admin_sessions = relationship("AdminSession", back_populates="admin", lazy="dynamic")
    badges = relationship("UserBadge", back_populates="user", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_supabase_id", "supabase_user_id"),
        Index("idx_user_role", "role"),
        Index("idx_user_plan", "plan"),
        Index("idx_user_is_active", "is_active"),
        Index("idx_user_email_verified", "email_verified"),
        Index("idx_user_profile_completed", "profile_completed"),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.admin.value
    
    @property
    def is_mod(self) -> bool:
        """Check if user has mod or admin role"""
        return self.role in (UserRole.mod.value, UserRole.admin.value)
    
    @property
    def is_premium(self) -> bool:
        """Check if user has a paid plan"""
        return self.plan in (UserPlan.standard.value, UserPlan.elite.value)

