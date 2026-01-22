"""Game model"""

from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class Game(Base):
    """Game model representing a sports game/match"""
    
    __tablename__ = "games"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    external_game_id = Column(String, unique=True, nullable=False, index=True)
    sport = Column(String, nullable=False, index=True)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="scheduled")  # scheduled, in_progress, final
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    markets = relationship("Market", back_populates="game", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_game_sport_start", "sport", "start_time"),
        Index("idx_game_status", "status"),
        Index("idx_games_sport_time_status", "sport", "start_time", "status"),
    )
    
    def __repr__(self):
        return f"<Game(id={self.id}, {self.away_team} @ {self.home_team})>"

