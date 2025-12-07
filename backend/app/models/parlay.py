"""Parlay model"""

from sqlalchemy import Column, String, Integer, Numeric, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class Parlay(Base):
    """Parlay model representing a generated parlay suggestion"""
    
    __tablename__ = "parlays"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True, index=True)  # Link to users table
    legs = Column(JSON, nullable=False)  # Array of leg objects with market_id, outcome, etc.
    num_legs = Column(Integer, nullable=False)
    model_version = Column(String, default="v1.0")
    parlay_hit_prob = Column(Numeric(5, 4), nullable=False)  # 0.0000 to 1.0000
    risk_profile = Column(String, nullable=False)  # conservative, balanced, degen
    ai_summary = Column(Text, nullable=True)
    ai_risk_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="parlays")
    
    # Indexes
    __table_args__ = (
        Index("idx_parlay_risk_profile", "risk_profile"),
        Index("idx_parlay_created", "created_at"),
        Index("idx_parlay_user", "user_id"),
    )
    
    def __repr__(self):
        return f"<Parlay(id={self.id}, {self.num_legs} legs, prob={self.parlay_hit_prob})>"

