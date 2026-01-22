"""Analysis page views model for traffic tracking."""

from sqlalchemy import Column, String, Integer, Date, DateTime, Index, ForeignKey
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class AnalysisPageViews(Base):
    """Track page views for analysis pages to enable props gating."""
    
    __tablename__ = "analysis_page_views"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(GUID(), ForeignKey("game_analyses.id"), nullable=False, index=True)
    game_id = Column(GUID(), ForeignKey("games.id"), nullable=False, index=True)
    league = Column(String, nullable=False, index=True)
    slug = Column(String, nullable=False, index=True)
    view_bucket_date = Column(Date, nullable=False, index=True)  # UTC date bucket
    views = Column(Integer, default=0, nullable=False)
    unique_visitors = Column(Integer, default=0, nullable=False)  # Optional for now
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Unique constraint on (analysis_id, view_bucket_date)
    __table_args__ = (
        Index("uq_analysis_page_views_analysis_date", "analysis_id", "view_bucket_date", unique=True),
        Index("idx_views_league_date", "league", "view_bucket_date"),
    )
    
    def __repr__(self):
        return f"<AnalysisPageViews(analysis_id={self.analysis_id}, date={self.view_bucket_date}, views={self.views})>"
