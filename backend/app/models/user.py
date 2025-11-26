"""User model for authentication and profiles"""

from sqlalchemy import Column, String, DateTime, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.session import Base


class User(Base):
    """User model for storing user profiles and preferences"""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supabase_user_id = Column(String, unique=True, nullable=False, index=True)  # Supabase auth user ID
    email = Column(String, nullable=False, index=True)
    username = Column(String, nullable=True)
    
    # User preferences
    default_risk_profile = Column(String, default="balanced")  # conservative, balanced, degen
    favorite_teams = Column(JSON, default=list)  # List of favorite team names
    favorite_sports = Column(JSON, default=list)  # List of favorite sports
    
    # Profile
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    parlays = relationship("Parlay", back_populates="user", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_supabase_id", "supabase_user_id"),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

