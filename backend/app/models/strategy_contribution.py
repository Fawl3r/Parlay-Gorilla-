"""
Per-prediction strategy contribution for ensemble decomposition.

Stores strategy_name, weight used, and contribution_value for each prediction.
Used for learning and leaderboard metrics.
"""

from sqlalchemy import Column, String, Float, Index, ForeignKey
import uuid

from app.database.session import Base
from app.database.types import GUID


class StrategyContribution(Base):
    __tablename__ = "strategy_contributions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(GUID(), ForeignKey("model_predictions.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy_name = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    contribution_value = Column(Float, nullable=False)

    __table_args__ = (Index("idx_strategy_contributions_prediction", "prediction_id"),)
