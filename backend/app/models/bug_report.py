"""Bug reports submitted by users (public-facing).

Keep this intentionally non-technical and safe:
- We store user-provided text + page context for triage.
- We DO NOT require auth (anonymous reports allowed).
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class BugSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class BugReport(Base):
    __tablename__ = "bug_reports"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    user_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_email = Column(String(255), nullable=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default=BugSeverity.medium.value, index=True)

    page_path = Column(String(300), nullable=True)
    page_url = Column(String(800), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Extra context like screen size, app version, etc.
    metadata_ = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("idx_bug_reports_created_at", "created_at"),
        Index("idx_bug_reports_severity_created_at", "severity", "created_at"),
    )




