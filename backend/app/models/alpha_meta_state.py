"""Alpha meta state: meta learning controller state (singleton)."""

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class AlphaMetaState(Base):
    """Singleton-ish state for meta learning controller."""
    __tablename__ = "alpha_meta_state"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    learning_paused = Column(Boolean, nullable=False, default=False)
    system_state = Column(String, nullable=True)  # PAUSED | ACTIVE | DEGRADED
    last_retrain_at = Column(DateTime(timezone=True), nullable=True)
    last_experiment_at = Column(DateTime(timezone=True), nullable=True)
    last_feature_discovery_at = Column(DateTime(timezone=True), nullable=True)
    last_alpha_research_at = Column(DateTime(timezone=True), nullable=True)
    last_experiment_eval_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(String, nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    correlation_id = Column(String, nullable=True)
    regime = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
