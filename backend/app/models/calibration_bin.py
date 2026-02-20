"""Calibration bins for lightweight monotonic calibration (no sklearn/torch)."""

from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.sql import func

from app.database.session import Base


class CalibrationBin(Base):
    """
    One bin of predicted_prob -> empirical hit rate.
    Used by calibration_service.calibrate(p) when mapping is trained.
    """

    __tablename__ = "calibration_bins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bin_index = Column(Integer, nullable=False)
    bin_low = Column(Float, nullable=False)
    bin_high = Column(Float, nullable=False)
    empirical_hit_rate = Column(Float, nullable=False)
    sample_count = Column(Integer, nullable=False)
    trained_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
