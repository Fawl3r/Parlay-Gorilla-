"""Market model"""

from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database.session import Base


class Market(Base):
    """Market model representing a betting market (moneyline, spread, total)"""
    
    __tablename__ = "markets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    market_type = Column(String, nullable=False)  # moneyline, spread, total
    book = Column(String, nullable=False)  # draftkings, fanduel, etc.
    
    # Relationships
    game = relationship("Game", back_populates="markets")
    odds = relationship("Odds", back_populates="market", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_market_game_type", "game_id", "market_type"),
        Index("idx_market_book", "book"),
    )
    
    def __repr__(self):
        return f"<Market(id={self.id}, {self.market_type} @ {self.book})>"

