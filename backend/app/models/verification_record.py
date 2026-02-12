"""Verification record model (hash-only, immutable from product perspective).

This table stores metadata for server-created verification records confirmed by the
verification worker.

It is intentionally append-only at the API layer:
- Records are created as `queued`
- The worker transitions them to `confirmed` or `failed`
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class VerificationStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"  # Claimed by verifier (Pattern A)
    confirmed = "confirmed"
    failed = "failed"


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    # Optional linkage to a Saved Parlay (older/manual flows).
    saved_parlay_id = Column(GUID(), ForeignKey("saved_parlays.id"), nullable=True, index=True)

    # Deterministic idempotency key for automatic custom parlay verification (sha256 hex).
    # DB-level hard stop: a fingerprint may be verified at most once.
    parlay_fingerprint = Column(String(64), nullable=True, index=True)

    # Deterministic hash (sha256 hex) of the canonical verification payload.
    data_hash = Column(String(64), nullable=False, index=True)

    status = Column(String(20), nullable=False, default=VerificationStatus.queued.value, index=True)

    # Immutable record identifiers from the proof layer.
    tx_digest = Column(String(128), nullable=True)
    object_id = Column(String(128), nullable=True)
    network = Column(String(20), nullable=False, default="mainnet")

    error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)

    # Retry/payment safety flags (prevents double-consuming quota/credits).
    quota_consumed = Column(Boolean, nullable=False, default=False)
    credits_consumed = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("parlay_fingerprint", name="unique_verification_records_parlay_fingerprint"),
        Index("idx_verification_records_user_created", "user_id", "created_at"),
        Index("idx_verification_records_saved_created", "saved_parlay_id", "created_at"),
        Index("idx_verification_records_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<VerificationRecord(id={self.id}, status={self.status}, saved_parlay_id={self.saved_parlay_id})>"


