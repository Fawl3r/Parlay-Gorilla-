"""System heartbeat model for proof of checking."""

from __future__ import annotations

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB

from app.database.session import Base


class SystemHeartbeat(Base):
    """System heartbeat model for tracking worker status."""
    
    __tablename__ = "system_heartbeats"
    
    name = Column(String, primary_key=True)  # scraper_worker, settlement_worker, etc.
    last_beat_at = Column(DateTime(timezone=True), nullable=False)
    meta = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)  # Stats: games_updated, parlays_settled, etc.
    
    def __repr__(self):
        return f"<SystemHeartbeat(name={self.name}, last_beat_at={self.last_beat_at})>"
