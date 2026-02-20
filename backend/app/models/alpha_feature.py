"""Alpha feature model: candidate/validated/rejected predictive features."""

from sqlalchemy import Column, String, Float, DateTime, Index
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class AlphaFeature(Base):
    """
    Stores discovered alpha features.
    status: TESTING | VALIDATED | REJECTED | DEPRECATED
    """
    __tablename__ = "alpha_features"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    feature_name = Column(String, nullable=False)
    feature_formula = Column(String, nullable=True)
    status = Column(String, nullable=False, default="TESTING")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    weight_cap = Column(Float, nullable=True)

    __table_args__ = (
        Index("idx_alpha_features_status", "status"),
        Index("idx_alpha_features_name", "feature_name", unique=True),
    )
