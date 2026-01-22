"""Watched game model for user watchlist."""

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class WatchedGame(Base):
    """Track games users have saved to their watchlist."""
    
    __tablename__ = "watched_games"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)  # Simple string for now (can be UUID later)
    game_id = Column(GUID(), ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    game = relationship("Game", backref="watched_by")
    
    # Indexes
    __table_args__ = (
        Index("idx_watched_game_user_game", "user_id", "game_id", unique=True),
        Index("idx_watched_game_user_created", "user_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<WatchedGame(user_id={self.user_id}, game_id={self.game_id})>"
