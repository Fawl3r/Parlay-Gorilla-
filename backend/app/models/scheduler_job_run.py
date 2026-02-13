"""Last-run status for scheduler jobs (ops visibility)."""

from __future__ import annotations

from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON

from app.database.session import Base


class SchedulerJobRun(Base):
    """Last run status per job for /ops/jobs."""

    __tablename__ = "scheduler_job_runs"

    job_name = Column(String(128), primary_key=True)
    last_run_at = Column(DateTime(timezone=True), nullable=False)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String(32), nullable=False)  # success, failure
    error_snippet = Column(Text, nullable=True)
    run_stats = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)  # e.g. injuries_provider_calls, injuries_records_written
