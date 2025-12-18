"""
ParlayPurchase model for tracking one-time parlay purchases.

Tracks pay-per-use parlay purchases for free users who have exhausted
their daily free parlays. Supports:
- $3 for single-sport parlay
- $5 for multi-sport parlay

Purchases expire after 24 hours if unused.
"""

from sqlalchemy import Column, String, DateTime, Index, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime, timezone, timedelta

from app.database.session import Base
from app.database.types import GUID


class ParlayType(str, enum.Enum):
    """Type of parlay purchase"""
    single = "single"  # Single-sport parlay ($3)
    multi = "multi"  # Multi-sport parlay ($5)


class PurchaseStatus(str, enum.Enum):
    """Status of parlay purchase"""
    pending = "pending"  # Payment initiated but not confirmed
    available = "available"  # Payment confirmed, ready to use
    used = "used"  # Parlay has been generated
    expired = "expired"  # Purchase expired (24h limit)
    refunded = "refunded"  # Purchase was refunded


class ParlayPurchase(Base):
    """
    One-time parlay purchase record.
    
    Tracks individual parlay purchases for pay-per-use model.
    Users can buy single parlays after exhausting their free daily limit.
    
    Pricing:
    - Single-sport parlay: $3
    - Multi-sport parlay: $5
    
    Purchases expire after 24 hours if unused.
    """
    
    __tablename__ = "parlay_purchases"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # User reference
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="parlay_purchases")
    
    # Payment reference (optional - linked when payment confirmed)
    payment_id = Column(GUID(), ForeignKey("payments.id"), nullable=True, index=True)
    payment = relationship("Payment")
    
    # Purchase details
    parlay_type = Column(String(20), nullable=False, index=True)  # single or multi
    amount = Column(Numeric(10, 2), nullable=False)  # Price paid (3.00 or 5.00)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Status tracking
    status = Column(String(20), default=PurchaseStatus.pending.value, nullable=False, index=True)
    
    # Provider tracking (for checkout session)
    provider = Column(String(50), nullable=True)  # lemonsqueezy or coinbase
    provider_checkout_id = Column(String(255), nullable=True, index=True)  # Checkout session ID
    
    # Usage tracking
    used_at = Column(DateTime(timezone=True), nullable=True)
    parlay_id = Column(GUID(), nullable=True)  # Link to generated parlay (if tracked)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)  # 24h after payment confirmation
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_parlay_purchases_user_status", "user_id", "status"),
        Index("idx_parlay_purchases_user_type_status", "user_id", "parlay_type", "status"),
        Index("idx_parlay_purchases_expires", "expires_at"),
    )
    
    def __repr__(self):
        return f"<ParlayPurchase(user={self.user_id}, type={self.parlay_type}, status={self.status})>"
    
    @property
    def is_available(self) -> bool:
        """Check if purchase is available for use"""
        if self.status != PurchaseStatus.available.value:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True
    
    @property
    def is_expired(self) -> bool:
        """Check if purchase has expired"""
        if self.status == PurchaseStatus.expired.value:
            return True
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return True
        return False
    
    @property
    def is_single_sport(self) -> bool:
        """Check if this is a single-sport parlay purchase"""
        return self.parlay_type == ParlayType.single.value
    
    @property
    def is_multi_sport(self) -> bool:
        """Check if this is a multi-sport parlay purchase"""
        return self.parlay_type == ParlayType.multi.value
    
    def mark_as_available(self, expiry_hours: int = 24) -> None:
        """Mark purchase as available after payment confirmation"""
        self.status = PurchaseStatus.available.value
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
    
    def mark_as_used(self, parlay_id: uuid.UUID = None) -> None:
        """Mark purchase as used after parlay generation"""
        self.status = PurchaseStatus.used.value
        self.used_at = datetime.now(timezone.utc)
        if parlay_id:
            self.parlay_id = parlay_id
    
    def mark_as_expired(self) -> None:
        """Mark purchase as expired"""
        self.status = PurchaseStatus.expired.value
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "parlay_type": self.parlay_type,
            "amount": float(self.amount),
            "currency": self.currency,
            "status": self.status,
            "is_available": self.is_available,
            "is_expired": self.is_expired,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "used_at": self.used_at.isoformat() if self.used_at else None,
        }




