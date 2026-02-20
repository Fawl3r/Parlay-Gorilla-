"""Alpha decay log: deprecation/decay events for validated features."""

from sqlalchemy import Column, String, Float, DateTime, Index
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class AlphaDecayLog(Base):
    """Log when a feature is deprecated due to performance decay."""
    __tablename__ = "alpha_decay_log"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    feature_id = Column(GUID(), nullable=True)
    feature_name = Column(String, nullable=True)
    reason = Column(String, nullable=False)
    ic_before = Column(Float, nullable=True)
    roi_before = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (Index("idx_alpha_decay_log_feature", "feature_id"),)
