"""
AffiliateCommission model for tracking commission earnings.

Records each commission earned by an affiliate from referred user purchases,
including subscription payments and credit pack purchases.
"""

from sqlalchemy import Column, String, DateTime, Index, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid
import enum

from app.database.session import Base
from app.database.types import GUID
from app.core.billing_config import COMMISSION_HOLD_DAYS


class CommissionStatus(str, enum.Enum):
    """Commission status enumeration"""
    PENDING = "pending"     # Within hold period
    READY = "ready"         # Ready for payout
    PAID = "paid"           # Paid to affiliate
    CANCELLED = "cancelled" # Cancelled (e.g., refund)


class CommissionSaleType(str, enum.Enum):
    """Type of sale that generated the commission"""
    SUBSCRIPTION = "subscription"
    CREDIT_PACK = "credit_pack"


class AffiliateCommission(Base):
    """
    Tracks commission earned on referred user purchases.
    
    Commission lifecycle:
    1. PENDING: Created when payment confirmed, within 30-day hold period
    2. READY: Hold period passed, eligible for payout
    3. PAID: Paid out to affiliate
    4. CANCELLED: If the original purchase was refunded
    
    Commission amounts are calculated based on affiliate's tier
    at the time of the sale.
    """
    
    __tablename__ = "affiliate_commissions"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Affiliate reference
    affiliate_id = Column(GUID(), ForeignKey("affiliates.id"), nullable=False, index=True)
    affiliate = relationship("Affiliate", back_populates="commissions")
    
    # Payout relationships (many-to-many)
    payouts = relationship(
        "AffiliatePayout",
        secondary="affiliate_payout_commissions",
        back_populates="commissions"
    )
    
    # Referred user who made the purchase
    referred_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    
    # Sale details
    sale_id = Column(String(255), nullable=False, index=True)  # Provider's payment/order ID
    sale_type = Column(String(20), nullable=False, index=True)  # subscription, credit_pack
    
    # Amounts
    base_amount = Column(Numeric(12, 2), nullable=False)  # Original sale amount
    commission_rate = Column(Numeric(5, 4), nullable=False)  # Rate applied (e.g., 0.20 for 20%)
    amount = Column(Numeric(12, 2), nullable=False)  # Commission amount
    currency = Column(String(3), default="USD", nullable=False)
    
    # Subscription-specific fields
    is_first_subscription_payment = Column(Boolean, default=False, nullable=False)
    subscription_plan = Column(String(50), nullable=True)
    
    # Credit pack specific fields
    credit_pack_id = Column(String(50), nullable=True)
    
    # Status tracking
    status = Column(String(20), default=CommissionStatus.PENDING.value, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    ready_at = Column(DateTime(timezone=True), nullable=True, index=True)  # When it becomes ready for payout
    paid_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Payout reference (if paid)
    payout_id = Column(String(255), nullable=True)
    payout_notes = Column(String(500), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_affiliate_commissions_affiliate_id", "affiliate_id"),
        Index("idx_affiliate_commissions_referred_user_id", "referred_user_id"),
        Index("idx_affiliate_commissions_sale_id", "sale_id"),
        Index("idx_affiliate_commissions_status", "status"),
        Index("idx_affiliate_commissions_ready_at", "ready_at"),
        Index("idx_affiliate_commissions_sale_type", "sale_type"),
    )
    
    def __repr__(self):
        return f"<AffiliateCommission(id={self.id}, amount={self.amount}, status={self.status})>"
    
    @classmethod
    def create_commission(
        cls,
        affiliate_id: uuid.UUID,
        referred_user_id: uuid.UUID,
        sale_id: str,
        sale_type: str,
        base_amount: Decimal,
        commission_rate: Decimal,
        is_first_subscription_payment: bool = False,
        subscription_plan: str = None,
        credit_pack_id: str = None,
        currency: str = "USD",
    ) -> "AffiliateCommission":
        """Create a new commission record with calculated ready_at date"""
        commission_amount = base_amount * commission_rate
        ready_at = datetime.now(timezone.utc) + timedelta(days=COMMISSION_HOLD_DAYS)
        
        return cls(
            id=uuid.uuid4(),
            affiliate_id=affiliate_id,
            referred_user_id=referred_user_id,
            sale_id=sale_id,
            sale_type=sale_type,
            base_amount=base_amount,
            commission_rate=commission_rate,
            amount=commission_amount,
            currency=currency,
            is_first_subscription_payment=is_first_subscription_payment,
            subscription_plan=subscription_plan,
            credit_pack_id=credit_pack_id,
            status=CommissionStatus.PENDING.value,
            ready_at=ready_at,
        )
    
    def mark_ready(self) -> None:
        """Mark commission as ready for payout"""
        if self.status == CommissionStatus.PENDING.value:
            self.status = CommissionStatus.READY.value
    
    def mark_paid(self, payout_id: str = None, notes: str = None) -> None:
        """Mark commission as paid"""
        self.status = CommissionStatus.PAID.value
        self.paid_at = datetime.now(timezone.utc)
        self.payout_id = payout_id
        self.payout_notes = notes
    
    def mark_cancelled(self, notes: str = None) -> None:
        """Mark commission as cancelled (e.g., due to refund)"""
        self.status = CommissionStatus.CANCELLED.value
        self.cancelled_at = datetime.now(timezone.utc)
        self.payout_notes = notes
    
    @property
    def is_ready_for_payout(self) -> bool:
        """Check if commission is ready for payout"""
        if self.status == CommissionStatus.READY.value:
            return True
        if self.status == CommissionStatus.PENDING.value and self.ready_at:
            return datetime.now(timezone.utc) >= self.ready_at
        return False
    
    @property
    def days_until_ready(self) -> int:
        """Days until commission becomes ready (0 if already ready)"""
        if self.status != CommissionStatus.PENDING.value:
            return 0
        if not self.ready_at:
            return 0
        delta = self.ready_at - datetime.now(timezone.utc)
        return max(0, delta.days)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "affiliate_id": str(self.affiliate_id),
            "referred_user_id": str(self.referred_user_id),
            "sale_id": self.sale_id,
            "sale_type": self.sale_type,
            "base_amount": float(self.base_amount),
            "commission_rate": float(self.commission_rate),
            "amount": float(self.amount),
            "currency": self.currency,
            "is_first_subscription_payment": self.is_first_subscription_payment,
            "subscription_plan": self.subscription_plan,
            "credit_pack_id": self.credit_pack_id,
            "status": self.status,
            "days_until_ready": self.days_until_ready,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ready_at": self.ready_at.isoformat() if self.ready_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "payout_id": self.payout_id,
        }




