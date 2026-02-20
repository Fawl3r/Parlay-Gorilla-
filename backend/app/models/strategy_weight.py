"""
Strategy weight model for RL-learned ensemble weights.

Persists strategy_name -> weight; updated by RL optimizer every N resolved predictions.
Weights sum to 1.0; no single strategy > 0.5 (enforced in service).
"""

from sqlalchemy import Column, String, Float, DateTime, Index
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class StrategyWeight(Base):
    __tablename__ = "strategy_weights"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    strategy_name = Column(String, nullable=False, index=True)
    weight = Column(Float, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (Index("idx_strategy_weights_name", "strategy_name", unique=True),)
