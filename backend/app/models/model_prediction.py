"""
Model Prediction tracking for learning and calibration.

Stores every prediction made by the model so we can:
- Track accuracy over time
- Calculate calibration errors
- Learn per-team biases
- Compare model versions
"""

from sqlalchemy import Column, String, Float, DateTime, JSON, Index
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class ModelPrediction(Base):
    """
    Stores individual predictions for tracking and learning.
    
    Each prediction captures:
    - The game and market being predicted
    - The probability output by the model
    - The market-implied probability for comparison
    - Model version for tracking improvements
    - Feature snapshot for debugging
    """
    
    __tablename__ = "model_predictions"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Game reference
    game_id = Column(GUID(), nullable=True, index=True)  # FK to games table
    external_game_id = Column(String, nullable=True, index=True)
    
    # Context
    sport = Column(String, nullable=False, index=True)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    game_time = Column(DateTime(timezone=True), nullable=True)
    
    # Prediction details
    market_type = Column(String, nullable=False)  # moneyline, spread, total
    team_side = Column(String, nullable=False)  # home, away, over, under
    
    # Probabilities
    predicted_prob = Column(Float, nullable=False)  # Model's predicted probability
    implied_prob = Column(Float, nullable=True)  # Market-implied probability
    edge = Column(Float, nullable=True)  # predicted_prob - implied_prob
    
    # Model info
    model_version = Column(String, nullable=False, default="pg-1.0.0")
    calculation_method = Column(String, nullable=True)  # odds_and_stats, stats_only, etc.
    confidence_score = Column(Float, nullable=True)  # 0-100
    
    # Feature snapshot (for debugging and retraining)
    feature_snapshot = Column(JSON, nullable=True)  # Store MatchupFeatureVector as JSON
    
    # Status
    is_resolved = Column(String, default="false")  # true/false
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_predictions_sport_date", "sport", "created_at"),
        Index("idx_predictions_model_version", "model_version"),
        Index("idx_predictions_resolved", "is_resolved"),
        Index("idx_predictions_team_side", "team_side", "sport"),
        Index("idx_predictions_game_market", "game_id", "market_type"),
    )
    
    def __repr__(self):
        return (
            f"<ModelPrediction("
            f"sport={self.sport}, "
            f"{self.away_team} @ {self.home_team}, "
            f"market={self.market_type}, "
            f"side={self.team_side}, "
            f"prob={self.predicted_prob:.3f}"
            f")>"
        )
    
    @property
    def has_edge(self) -> bool:
        """Check if prediction has positive edge"""
        if self.edge is None:
            return False
        return self.edge > 0
    
    @property
    def edge_percentage(self) -> float:
        """Get edge as percentage"""
        return (self.edge or 0) * 100

