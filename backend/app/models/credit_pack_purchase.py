"""
CreditPackPurchase model for purchase-level idempotency of credit pack fulfillment.

Why this exists:
- Payment providers can send duplicate webhooks (retries) and/or multiple events per order.
- We must never double-award credits for the same provider order/charge.

This table records each fulfilled credit pack purchase with a uniqueness constraint on
(`provider`, `provider_order_id`).
"""

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import enum
import uuid

from app.database.session import Base
from app.database.types import GUID


class CreditPackPurchaseStatus(str, enum.Enum):
    """Status of a credit pack purchase."""

    fulfilled = "fulfilled"
    refunded = "refunded"


class CreditPackPurchase(Base):
    """
    Fulfilled credit pack purchase.

    A row is inserted when credits are awarded to a user.
    """

    __tablename__ = "credit_pack_purchases"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # User reference
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="credit_pack_purchases")

    # Provider tracking
    provider = Column(String(50), nullable=False, index=True)  # lemonsqueezy | coinbase
    provider_order_id = Column(String(255), nullable=False)  # order/charge ID from provider

    # Pack tracking
    credit_pack_id = Column(String(50), nullable=False, index=True)  # credits_10, credits_25, ...
    credits_awarded = Column(Integer, nullable=False)

    # Amount tracking (for audit + affiliate reporting)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    status = Column(String(20), default=CreditPackPurchaseStatus.fulfilled.value, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    fulfilled_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("provider", "provider_order_id", name="uq_credit_pack_purchases_provider_order_id"),
        Index("idx_credit_pack_purchases_user_created_at", "user_id", "created_at"),
        Index("idx_credit_pack_purchases_provider_created_at", "provider", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<CreditPackPurchase(provider={self.provider}, provider_order_id={self.provider_order_id}, "
            f"user_id={self.user_id}, credit_pack_id={self.credit_pack_id}, status={self.status})>"
        )

    def mark_fulfilled_now(self) -> None:
        self.status = CreditPackPurchaseStatus.fulfilled.value
        self.fulfilled_at = datetime.now(timezone.utc)


