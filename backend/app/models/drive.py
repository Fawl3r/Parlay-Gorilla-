"""Drive model for tracking game drives/possessions"""

from sqlalchemy import Column, String, Integer, DateTime, Index, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database.session import Base
from app.database.types import GUID


class DriveResult(str, enum.Enum):
    """Possible results of a drive"""
    touchdown = "touchdown"
    field_goal = "field_goal"
    punt = "punt"
    turnover = "turnover"
    turnover_on_downs = "turnover_on_downs"
    safety = "safety"
    end_of_half = "end_of_half"
    end_of_game = "end_of_game"
    in_progress = "in_progress"
    # Basketball/Hockey specific
    score = "score"
    miss = "miss"
    turnover_live = "turnover_live"


class Drive(Base):
    """
    Drive model for tracking individual possessions/drives in a game.
    
    Primarily used for football (NFL), but can track possessions
    for other sports as well.
    """
    
    __tablename__ = "drives"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to live game
    game_id = Column(GUID(), ForeignKey("live_games.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Drive identification
    drive_number = Column(Integer, nullable=False)
    external_drive_id = Column(String(255), nullable=True, unique=True)  # Provider drive ID
    
    # Team on possession
    team = Column(String(100), nullable=False)
    team_id = Column(String(100), nullable=True)  # Provider team ID
    is_home_team = Column(Integer, default=0)  # 1 = home, 0 = away
    
    # Drive details
    quarter = Column(Integer, nullable=True)  # Which quarter/period
    start_time = Column(String(20), nullable=True)  # Time when drive started
    end_time = Column(String(20), nullable=True)  # Time when drive ended
    
    # Field position (for football)
    start_yard_line = Column(Integer, nullable=True)
    end_yard_line = Column(Integer, nullable=True)
    yards_gained = Column(Integer, nullable=True)
    plays_count = Column(Integer, nullable=True)
    
    # Result
    result = Column(String(50), nullable=True)  # DriveResult value
    points_scored = Column(Integer, default=0)
    
    # Description - human readable summary
    description = Column(Text, nullable=True)
    
    # Score after this drive
    home_score_after = Column(Integer, nullable=True)
    away_score_after = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    live_game = relationship("LiveGame", back_populates="drives")
    
    # Indexes
    __table_args__ = (
        Index("idx_drive_game_number", "game_id", "drive_number"),
        Index("idx_drive_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<Drive(id={self.id}, game={self.game_id}, #{self.drive_number}, result={self.result})>"
    
    @property
    def is_scoring_drive(self) -> bool:
        """Check if this drive resulted in points"""
        return self.points_scored > 0 if self.points_scored else False
    
    def to_telegram_message(self) -> str:
        """Format drive for Telegram notification"""
        emoji = "🏈" if self.result in ["touchdown", "field_goal"] else "📍"
        if self.result == "touchdown":
            emoji = "🎉"
        elif self.result == "field_goal":
            emoji = "🥅"
        elif self.result == "turnover":
            emoji = "↩️"
        
        msg = f"{emoji} {self.team}"
        if self.description:
            msg += f"\n{self.description}"
        if self.points_scored and self.points_scored > 0:
            msg += f"\n+{self.points_scored} points"
        if self.home_score_after is not None and self.away_score_after is not None:
            msg += f"\nScore: {self.away_score_after} - {self.home_score_after}"
        
        return msg

