"""Daily API quota usage per sport (DB fallback when Redis unavailable)."""

from __future__ import annotations

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func

from app.database.session import Base


class ApiQuotaUsage(Base):
    """Tracks daily request usage per sport for API-Sports when Redis is not used."""

    __tablename__ = "api_quota_usage"

    date = Column(String(10), primary_key=True)  # YYYY-MM-DD (America/Chicago)
    sport = Column(String(16), primary_key=True)  # NFL, NBA, default, etc.
    used = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
