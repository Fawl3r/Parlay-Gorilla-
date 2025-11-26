"""Team statistics model for historical performance tracking"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database.session import Base


class TeamStats(Base):
    """Team statistics for a season/week"""
    
    __tablename__ = "team_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_name = Column(String, nullable=False, index=True)
    season = Column(String, nullable=False)  # e.g., "2024"
    week = Column(Integer, nullable=True)  # Week number, null for season totals
    
    # Record
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    ties = Column(Integer, default=0)
    win_percentage = Column(Float, default=0.0)
    
    # Offensive stats
    points_per_game = Column(Float, default=0.0)
    yards_per_game = Column(Float, default=0.0)
    passing_yards_per_game = Column(Float, default=0.0)
    rushing_yards_per_game = Column(Float, default=0.0)
    
    # Defensive stats
    points_allowed_per_game = Column(Float, default=0.0)
    yards_allowed_per_game = Column(Float, default=0.0)
    turnovers_forced = Column(Integer, default=0)
    
    # Recent form (last N games)
    recent_wins = Column(Integer, default=0)  # Wins in last 5 games
    recent_losses = Column(Integer, default=0)
    home_record_wins = Column(Integer, default=0)
    home_record_losses = Column(Integer, default=0)
    away_record_wins = Column(Integer, default=0)
    away_record_losses = Column(Integer, default=0)
    
    # Strength metrics (calculated)
    offensive_rating = Column(Float, default=0.0)
    defensive_rating = Column(Float, default=0.0)
    overall_rating = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index("idx_team_stats_team_season", "team_name", "season"),
        Index("idx_team_stats_season_week", "season", "week"),
    )
    
    def __repr__(self):
        return f"<TeamStats(team={self.team_name}, season={self.season}, wins={self.wins}-{self.losses})>"

