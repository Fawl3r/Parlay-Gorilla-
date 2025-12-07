"""Game analysis model for Covers-style AI breakdowns"""

from sqlalchemy import Column, String, DateTime, Text, Index, ForeignKey, Integer, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database.session import Base
from app.database.types import GUID


class GameAnalysis(Base):
    """Pre-generated AI analysis for a game (Covers-style breakdown)"""
    
    __tablename__ = "game_analyses"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    game_id = Column(GUID(), ForeignKey("games.id"), nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)  # e.g., "bears-vs-packers-week-14-2025"
    league = Column(String, nullable=False, index=True)  # NFL, NBA, MLB, NHL
    matchup = Column(String, nullable=False)  # "Chicago Bears @ Green Bay Packers"
    
    # Full analysis content as structured JSON
    analysis_content = Column(JSON, nullable=False)  # Contains all sections: summary, picks, parlays, etc.
    
    # SEO metadata
    seo_metadata = Column(JSON, nullable=True)  # title, description, keywords, etc.
    
    # Generation tracking
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # When analysis should be regenerated
    version = Column(Integer, default=1)  # Increment when regenerated
    
    # Relationships
    game = relationship("Game", backref="analyses")
    
    # Indexes
    __table_args__ = (
        Index("idx_game_analysis_slug", "slug"),
        Index("idx_game_analysis_league", "league"),
        Index("idx_game_analysis_expires", "expires_at"),
        Index("idx_game_analysis_game_league", "game_id", "league"),
    )
    
    def __repr__(self):
        return f"<GameAnalysis(slug={self.slug}, league={self.league}, version={self.version})>"

