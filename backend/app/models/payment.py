"""
Payment model for revenue tracking.

Stores payment records from LemonSqueezy, Coinbase Commerce, or other providers.
Designed as a stub ready for webhook integration.
"""

from sqlalchemy import Column, String, DateTime, Index, ForeignKey, Numeric, Text
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database.session import Base
from app.database.types import GUID


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration"""
    pending = "pending"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"
    disputed = "disputed"


class PaymentProvider(str, enum.Enum):
    """Payment provider enumeration"""
    lemonsqueezy = "lemonsqueezy"
    coinbase_commerce = "coinbase_commerce"
    stripe = "stripe"
    manual = "manual"  # For admin-granted access


class Payment(Base):
    """
    Payment record tracking.
    
    Stores individual payment transactions for revenue analytics.
    Ready for LemonSqueezy/Coinbase Commerce webhook integration.
    
    Webhook integration TODO:
    - LemonSqueezy: Listen for `order_created`, `subscription_payment_success`
    - Coinbase Commerce: Listen for `charge:confirmed`, `charge:failed`
    """
    
    __tablename__ = "payments"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # User reference
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="payments")
    
    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)  # ISO 4217
    
    # Plan purchased
    plan = Column(String(50), nullable=False)  # standard, elite, etc.
    
    # Provider details
    provider = Column(String(50), nullable=False, index=True)  # lemonsqueezy, coinbase_commerce
    provider_payment_id = Column(String(255), nullable=True, unique=True, index=True)
    provider_order_id = Column(String(255), nullable=True, index=True)
    
    # Status
    status = Column(String(20), default=PaymentStatus.pending.value, nullable=False, index=True)
    
    # Provider raw response (for debugging/auditing)
    provider_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Indexes for analytics
    __table_args__ = (
        Index("idx_payments_user_date", "user_id", "created_at"),
        Index("idx_payments_status_date", "status", "created_at"),
        Index("idx_payments_provider_date", "provider", "created_at"),
        Index("idx_payments_plan", "plan"),
    )
    
    def __repr__(self):
        return f"<Payment(user={self.user_id}, amount={self.amount} {self.currency}, status={self.status})>"
    
    @property
    def is_successful(self) -> bool:
        """Check if payment was successful"""
        return self.status == PaymentStatus.paid.value

