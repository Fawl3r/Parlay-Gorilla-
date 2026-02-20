"""Alpha strategy graph node: predictive signal with weight."""

from sqlalchemy import Column, String, Float, DateTime, Index
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class AlphaStrategyNode(Base):
    """Node in strategy graph: one predictive signal."""
    __tablename__ = "alpha_strategy_nodes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    signal_name = Column(String, nullable=False)
    weight = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (Index("idx_alpha_strategy_nodes_signal", "signal_name", unique=True),)
