"""Odds model"""

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class Odds(Base):
    """Odds model representing specific odds for a market outcome"""
    
    __tablename__ = "odds"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    market_id = Column(GUID(), ForeignKey("markets.id", ondelete="CASCADE"), nullable=False)
    outcome = Column(String, nullable=False)  # home, away, over, under, etc.
    price = Column(String, nullable=False)  # American odds format (e.g., "+150", "-110")
    decimal_price = Column(Numeric(10, 3), nullable=False)
    implied_prob = Column(Numeric(5, 4), nullable=False)  # 0.0000 to 1.0000
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    market = relationship("Market", back_populates="odds")
    
    # Indexes
    __table_args__ = (
        Index("idx_odds_market_created", "market_id", "created_at"),
        Index("idx_odds_implied_prob", "implied_prob"),
    )
    
    def __repr__(self):
        return f"<Odds(id={self.id}, {self.outcome} @ {self.price})>"

