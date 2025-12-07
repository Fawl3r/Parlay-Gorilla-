"""
Prediction Outcome tracking for learning and calibration.

Links predictions to their actual outcomes so we can:
- Calculate accuracy metrics
- Track calibration errors
- Build per-team bias adjustments
"""

from sqlalchemy import Column, String, Float, Boolean, DateTime, Index, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database.session import Base
from app.database.types import GUID


class PredictionOutcome(Base):
    """
    Links a ModelPrediction to its actual outcome.
    
    Enables:
    - Accuracy calculation
    - Brier score calculation
    - Calibration analysis
    - Per-team bias tracking
    """
    
    __tablename__ = "prediction_outcomes"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Link to prediction
    prediction_id = Column(GUID(), ForeignKey("model_predictions.id"), nullable=False, index=True)
    
    # Outcome
    was_correct = Column(Boolean, nullable=False)  # Did the prediction hit?
    
    # Error metrics
    error_magnitude = Column(Float, nullable=False)  # |predicted_prob - actual_outcome|
    signed_error = Column(Float, nullable=False)  # predicted_prob - actual_outcome (for bias)
    
    # Additional context
    actual_result = Column(String, nullable=True)  # "home", "away", "over", "under", "push"
    actual_score_home = Column(Float, nullable=True)
    actual_score_away = Column(Float, nullable=True)
    
    # Timestamps
    resolved_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index("idx_outcomes_prediction", "prediction_id"),
        Index("idx_outcomes_correct", "was_correct"),
        Index("idx_outcomes_resolved", "resolved_at"),
    )
    
    def __repr__(self):
        result = "✓" if self.was_correct else "✗"
        return (
            f"<PredictionOutcome("
            f"prediction={self.prediction_id}, "
            f"result={result}, "
            f"error={self.error_magnitude:.3f}"
            f")>"
        )


class TeamCalibration(Base):
    """
    Stores per-team calibration adjustments.
    
    Updated periodically based on prediction outcomes to correct
    for systematic over/under-rating of specific teams.
    """
    
    __tablename__ = "team_calibrations"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Team identification
    team_name = Column(String, nullable=False, index=True)
    sport = Column(String, nullable=False, index=True)
    
    # Calibration values
    bias_adjustment = Column(Float, default=0.0)  # Add to raw probability
    avg_signed_error = Column(Float, default=0.0)  # Average over/under-prediction
    
    # Sample size for confidence
    sample_size = Column(Float, default=0)  # Number of games used
    
    # Quality metrics
    accuracy = Column(Float, nullable=True)  # Overall accuracy for this team
    brier_score = Column(Float, nullable=True)  # Brier score for this team
    
    # Timestamps
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Unique constraint
    __table_args__ = (
        Index("idx_calibration_team_sport", "team_name", "sport", unique=True),
    )
    
    def __repr__(self):
        adj_str = f"+{self.bias_adjustment:.3f}" if self.bias_adjustment >= 0 else f"{self.bias_adjustment:.3f}"
        return (
            f"<TeamCalibration("
            f"team={self.team_name}, "
            f"sport={self.sport}, "
            f"adjustment={adj_str}, "
            f"n={self.sample_size}"
            f")>"
        )
    
    @property
    def is_reliable(self) -> bool:
        """Check if calibration has enough samples to be reliable"""
        return self.sample_size >= 10
    
    @property
    def clamped_adjustment(self) -> float:
        """Get bias adjustment clamped to reasonable range"""
        return max(-0.05, min(0.05, self.bias_adjustment))

