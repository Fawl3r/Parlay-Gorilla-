"""Game model"""

from sqlalchemy import Column, String, DateTime, Index, Integer, Boolean
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
    external_game_key = Column(String, nullable=True, unique=True, index=True)  # Scraper identifier
    sport = Column(String, nullable=False, index=True)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="scheduled")  # scheduled, in_progress, final, LIVE, FINAL
    
    # Live score fields (added via migration)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    period = Column(String, nullable=True)  # Q3, 2nd, 7th inning, etc.
    clock = Column(String, nullable=True)  # 04:12, etc.
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    data_source = Column(String, nullable=True)  # espn, yahoo, etc.
    is_stale = Column(Boolean, default=False, nullable=False)
    
    # Season phase / playoff metadata (provider-driven; never infer from date alone)
    season_phase = Column(String, nullable=True)  # "preseason" | "regular" | "postseason"
    stage = Column(String, nullable=True)        # provider stage text (e.g. "Playoffs", "Wildcard")
    round_ = Column("round", String, nullable=True)  # provider round label
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    markets = relationship("Market", back_populates="game", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_game_sport_start", "sport", "start_time"),
        Index("idx_game_status", "status"),
        Index("idx_games_sport_time_status", "sport", "start_time", "status"),
        Index("idx_games_sport_season_phase", "sport", "season_phase"),
    )
    
    def __repr__(self):
        return f"<Game(id={self.id}, {self.away_team} @ {self.home_team})>"

