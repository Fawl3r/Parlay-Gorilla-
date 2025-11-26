"""Market efficiency model for tracking odds across books"""

from sqlalchemy import Column, String, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database.session import Base


class MarketEfficiency(Base):
    """Track odds across different books to detect market inefficiencies"""
    
    __tablename__ = "market_efficiency"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    market_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    sport = Column(String, nullable=False)
    market_type = Column(String, nullable=False)  # h2h, spreads, totals
    outcome = Column(String, nullable=False)
    
    # Odds from different books
    book_name = Column(String, nullable=False)
    american_odds = Column(String, nullable=True)  # e.g., "-110"
    decimal_odds = Column(Float, nullable=False)
    implied_probability = Column(Float, nullable=False)
    
    # Market analysis
    best_odds = Column(Float, nullable=True)  # Best decimal odds available
    worst_odds = Column(Float, nullable=True)  # Worst decimal odds available
    average_odds = Column(Float, nullable=True)  # Average across all books
    odds_variance = Column(Float, nullable=True)  # Variance in odds (higher = less efficient)
    
    # Value detection
    has_value = Column(String, default="false")  # "true" if significant value detected
    value_score = Column(Float, nullable=True)  # Calculated value score
    
    # Timestamp
    snapshot_time = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index("idx_market_efficiency_game_market", "game_id", "market_id"),
        Index("idx_market_efficiency_snapshot", "snapshot_time"),
        Index("idx_market_efficiency_value", "has_value"),
    )
    
    def __repr__(self):
        return f"<MarketEfficiency(book={self.book_name}, odds={self.decimal_odds}, prob={self.implied_probability:.2%})>"

