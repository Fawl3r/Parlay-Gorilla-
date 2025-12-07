"""Parlay cache model for storing pre-calculated parlay probabilities"""

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Index, JSON
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class ParlayCache(Base):
    """Cache for pre-calculated parlay suggestions"""
    
    __tablename__ = "parlay_cache"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Cache key components
    num_legs = Column(Integer, nullable=False, index=True)
    risk_profile = Column(String, nullable=False, index=True)  # conservative, balanced, degen
    sport = Column(String, default="NFL", index=True)
    
    # Cached data
    cached_parlay_data = Column(JSON, nullable=False)  # Full parlay data structure
    cached_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Cache metadata
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    hit_count = Column(Integer, default=0)  # Number of times this cache was used
    
    # Indexes for efficient lookups
    __table_args__ = (
        Index("idx_parlay_cache_lookup", "num_legs", "risk_profile", "sport", "expires_at"),
    )
    
    def __repr__(self):
        return f"<ParlayCache(id={self.id}, {self.num_legs} legs, {self.risk_profile})>"

