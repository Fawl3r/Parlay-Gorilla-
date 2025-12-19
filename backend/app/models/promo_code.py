"""Promo code model for one-time promotions (credits or premium time)."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class PromoRewardType(str, enum.Enum):
    """Supported promo rewards."""

    premium_month = "premium_month"
    credits_3 = "credits_3"


class PromoCode(Base):
    """
    Promo codes can be redeemed by authenticated users.

    Rules:
    - Must be active
    - Must not be expired
    - Must not exceed max_uses_total
    - Can only be redeemed once per user (enforced via PromoRedemption unique constraint)
    """

    __tablename__ = "promo_codes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Human-shareable code (e.g., PG-ABCD-EFGH)
    code = Column(String(length=64), nullable=False, unique=True, index=True)

    # Reward type (fixed set; see PromoRewardType)
    reward_type = Column(String(length=32), nullable=False, index=True)

    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Total number of redemptions allowed across all users.
    max_uses_total = Column(Integer, nullable=False, default=1)

    # Denormalized counter to enforce max_uses_total without heavy aggregation.
    redeemed_count = Column(Integer, nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True, index=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)

    created_by_user_id = Column(GUID(), ForeignKey("users.id"), nullable=True, index=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    redemptions = relationship("PromoRedemption", back_populates="promo_code", lazy="dynamic")

    __table_args__ = (
        Index("ix_promo_codes_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PromoCode(id={self.id}, code={self.code}, reward_type={self.reward_type})>"

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        expires_at = self.expires_at
        # SQLite may return naive datetimes; treat as UTC.
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at <= datetime.now(timezone.utc)


