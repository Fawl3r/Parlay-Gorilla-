"""
Model health state for drift detection and auto-correction.

Tracks: GREEN / YELLOW / RED, health_score, rolling_roi, last_rl_update, calibration_version.
Single row (singleton) updated by model_health_service.
"""

from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class ModelHealthState(Base):
    __tablename__ = "model_health_state"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    model_state = Column(String, nullable=False, server_default="GREEN")  # GREEN | YELLOW | RED
    health_score = Column(Float, nullable=True)
    rolling_roi = Column(Float, nullable=True)
    last_rl_update_at = Column(DateTime(timezone=True), nullable=True)
    calibration_version = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
