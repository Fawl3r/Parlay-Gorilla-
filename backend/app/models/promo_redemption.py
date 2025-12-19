"""Promo code redemption audit model."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class PromoRedemption(Base):
    """
    Tracks a user's redemption of a promo code.

    Uniqueness:
    - A user can redeem a specific promo code only once (promo_code_id + user_id).
    """

    __tablename__ = "promo_redemptions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    promo_code_id = Column(GUID(), ForeignKey("promo_codes.id"), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)

    # Denormalized for audit/debugging (kept in sync at redemption time)
    reward_type = Column(String(length=32), nullable=False)

    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(length=64), nullable=True)

    redeemed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    promo_code = relationship("PromoCode", back_populates="redemptions")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("promo_code_id", "user_id", name="uq_promo_redemptions_code_user"),
        Index("ix_promo_redemptions_created_at", "redeemed_at"),
    )

    def __repr__(self) -> str:
        return f"<PromoRedemption(id={self.id}, promo_code_id={self.promo_code_id}, user_id={self.user_id})>"


