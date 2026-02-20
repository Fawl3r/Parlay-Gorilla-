"""Alpha experiment model: A/B experiment runs with metrics."""

from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer, Index
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class AlphaExperiment(Base):
    """A/B experiment: Group A = production, Group B = model + new alpha feature."""
    __tablename__ = "alpha_experiments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    feature_id = Column(GUID(), nullable=True)
    experiment_name = Column(String, nullable=False)
    group_a_accuracy = Column(Float, nullable=True)
    group_b_accuracy = Column(Float, nullable=True)
    group_a_brier_score = Column(Float, nullable=True)
    group_b_brier_score = Column(Float, nullable=True)
    group_a_clv = Column(Float, nullable=True)
    group_b_clv = Column(Float, nullable=True)
    group_a_roi = Column(Float, nullable=True)
    group_b_roi = Column(Float, nullable=True)
    sample_size_a = Column(Integer, nullable=True)
    sample_size_b = Column(Integer, nullable=True)
    p_value = Column(Float, nullable=True)
    promoted = Column(Boolean, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    correlation_id = Column(String, nullable=True)

    __table_args__ = (
        Index("idx_alpha_experiments_feature", "feature_id"),
        Index("idx_alpha_experiments_started", "started_at"),
    )
