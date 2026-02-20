"""Alpha strategy graph edge: interaction strength between signals."""

from sqlalchemy import Column, String, Float, DateTime, Index
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class AlphaStrategyEdge(Base):
    """Edge between two strategy nodes: interaction_strength."""
    __tablename__ = "alpha_strategy_edges"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    from_node_id = Column(GUID(), nullable=False)
    to_node_id = Column(GUID(), nullable=False)
    interaction_strength = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_alpha_strategy_edges_from", "from_node_id"),
        Index("idx_alpha_strategy_edges_to", "to_node_id"),
    )
