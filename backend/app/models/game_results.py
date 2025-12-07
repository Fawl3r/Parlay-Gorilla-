"""Game results model for storing actual game outcomes"""

from sqlalchemy import Column, String, Integer, DateTime, Float, Index
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class GameResult(Base):
    """Actual game results for training and evaluation"""
    
    __tablename__ = "game_results"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    game_id = Column(GUID(), nullable=True, index=True)  # Link to games table
    external_game_id = Column(String, nullable=True, index=True)
    
    sport = Column(String, nullable=False, index=True)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    game_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Final scores
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    
    # Outcomes
    winner = Column(String, nullable=True)  # "home" or "away"
    home_covered_spread = Column(String, nullable=True)  # "yes", "no", "push"
    total_over_under = Column(String, nullable=True)  # "over", "under", "push"
    actual_total = Column(Integer, nullable=True)
    spread_line = Column(Float, nullable=True)  # The spread that was used
    total_line = Column(Float, nullable=True)  # The total that was used
    
    # Game context (for analysis)
    weather_condition = Column(String, nullable=True)
    temperature = Column(Float, nullable=True)
    attendance = Column(Integer, nullable=True)
    
    # Status
    status = Column(String, default="final")  # final, cancelled, postponed
    completed = Column(String, default="true")  # true/false
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index("idx_game_results_sport_date", "sport", "game_date"),
        Index("idx_game_results_completed", "completed"),
    )
    
    def __repr__(self):
        return f"<GameResult({self.away_team} @ {self.home_team}, {self.away_score}-{self.home_score})>"

