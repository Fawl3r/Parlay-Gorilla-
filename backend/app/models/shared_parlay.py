"""Shared parlay model for social features"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.session import Base


class SharedParlay(Base):
    """Model for shared parlays (social feature)"""
    
    __tablename__ = "shared_parlays"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parlay_id = Column(UUID(as_uuid=True), ForeignKey("parlays.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Sharing metadata
    share_token = Column(String, unique=True, nullable=False, index=True)  # Unique token for sharing
    is_public = Column(String, default="public")  # public, unlisted, private
    views_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    
    # Optional comment/note
    comment = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    parlay = relationship("Parlay", backref="shared_instances")
    user = relationship("User", backref="shared_parlays")
    
    # Indexes
    __table_args__ = (
        Index("idx_shared_parlay_token", "share_token"),
        Index("idx_shared_parlay_user", "user_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<SharedParlay(id={self.id}, parlay_id={self.parlay_id})>"


class ParlayLike(Base):
    """Model for parlay likes"""
    
    __tablename__ = "parlay_likes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shared_parlay_id = Column(UUID(as_uuid=True), ForeignKey("shared_parlays.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index("idx_parlay_like_unique", "shared_parlay_id", "user_id", unique=True),
    )
    
    def __repr__(self):
        return f"<ParlayLike(id={self.id}, shared_parlay_id={self.shared_parlay_id})>"

