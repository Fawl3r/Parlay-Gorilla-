"""Daily API quota usage (DB fallback when Redis unavailable)."""

from __future__ import annotations

from sqlalchemy import Column, String, Integer, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from app.database.session import Base


class ApiQuotaUsage(Base):
    """Tracks daily request usage for API-Sports when Redis is not used."""

    __tablename__ = "api_quota_usage"

    date = Column(String(10), primary_key=True)  # YYYY-MM-DD (America/Chicago)
    used = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
