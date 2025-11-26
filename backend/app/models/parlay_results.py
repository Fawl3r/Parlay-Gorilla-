"""Parlay results model for tracking parlay performance"""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database.session import Base


class ParlayResult(Base):
    """Track parlay outcomes for performance analysis"""
    
    __tablename__ = "parlay_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parlay_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Link to parlays table
    
    # Parlay details
    num_legs = Column(Integer, nullable=False)
    risk_profile = Column(String, nullable=False)
    model_version = Column(String, default="v0_heuristic")
    
    # Predicted values
    predicted_probability = Column(Float, nullable=False)
    predicted_confidence = Column(Float, nullable=False)
    
    # Actual outcome
    hit = Column(Boolean, nullable=True)  # True if parlay won, False if lost, None if pending
    legs_hit = Column(Integer, default=0)  # Number of legs that hit
    legs_missed = Column(Integer, default=0)  # Number of legs that missed
    
    # Leg outcomes (JSON array of leg results)
    leg_results = Column(JSON, nullable=True)  # [{"leg_id": "...", "hit": true/false, ...}]
    
    # Performance metrics
    actual_probability = Column(Float, nullable=True)  # Calculated from actual results
    calibration_error = Column(Float, nullable=True)  # |predicted - actual|
    roi = Column(Float, nullable=True)  # Return on investment if bet was placed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)  # When all games finished
    
    # Indexes
    __table_args__ = (
        Index("idx_parlay_results_hit", "hit"),
        Index("idx_parlay_results_model", "model_version"),
        Index("idx_parlay_results_risk", "risk_profile"),
        Index("idx_parlay_results_created", "created_at"),
    )
    
    def __repr__(self):
        status = "pending" if self.hit is None else ("hit" if self.hit else "missed")
        return f"<ParlayResult(id={self.id}, {self.num_legs} legs, {status})>"

