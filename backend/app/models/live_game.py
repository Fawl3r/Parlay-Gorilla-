"""Live Game model for real-time game tracking"""

from sqlalchemy import Column, String, Integer, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database.session import Base
from app.database.types import GUID


class LiveGameStatus(str, enum.Enum):
    """Status of a live game"""
    scheduled = "scheduled"
    in_progress = "in_progress"
    halftime = "halftime"
    final = "final"
    postponed = "postponed"
    cancelled = "cancelled"


class LiveGame(Base):
    """
    Live Game model for real-time game state tracking.
    
    Tracks scores, quarter/period, time remaining, and syncs with
    SportsRadar API for live updates.
    """
    
    __tablename__ = "live_games"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # External reference - links to SportsRadar game ID
    external_game_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Sport type (nfl, nba, nhl, mlb, soccer)
    sport = Column(String(50), nullable=False, index=True)
    
    # Teams
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    home_team_id = Column(String(100), nullable=True)  # SportsRadar team ID
    away_team_id = Column(String(100), nullable=True)  # SportsRadar team ID
    
    # Game status
    status = Column(String(50), default=LiveGameStatus.scheduled.value, nullable=False, index=True)
    
    # Current game state
    quarter = Column(Integer, nullable=True)  # Current quarter/period/inning
    period_name = Column(String(50), nullable=True)  # "1st Quarter", "2nd Period", etc.
    time_remaining = Column(String(20), nullable=True)  # "12:45", "5:30", etc.
    
    # Scores
    home_score = Column(Integer, default=0, nullable=False)
    away_score = Column(Integer, default=0, nullable=False)
    
    # Game schedule
    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    drives = relationship("Drive", back_populates="live_game", cascade="all, delete-orphan")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_live_game_status_sport", "status", "sport"),
        Index("idx_live_game_last_updated", "last_updated_at"),
        Index("idx_live_game_scheduled_start", "scheduled_start"),
    )
    
    def __repr__(self):
        return f"<LiveGame(id={self.id}, {self.away_team} @ {self.home_team}, status={self.status})>"
    
    @property
    def is_live(self) -> bool:
        """Check if game is currently in progress"""
        return self.status == LiveGameStatus.in_progress.value
    
    @property
    def is_final(self) -> bool:
        """Check if game has ended"""
        return self.status == LiveGameStatus.final.value
    
    @property
    def score_display(self) -> str:
        """Get formatted score display"""
        return f"{self.away_team} {self.away_score} - {self.home_score} {self.home_team}"

