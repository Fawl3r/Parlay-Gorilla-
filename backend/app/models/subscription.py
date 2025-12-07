"""
Subscription model for active subscription tracking.

Tracks user subscription status, billing cycles, and cancellations.
Designed for LemonSqueezy/Coinbase Commerce integration.
"""

from sqlalchemy import Column, String, DateTime, Index, ForeignKey, Boolean
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database.session import Base
from app.database.types import GUID


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enumeration"""
    active = "active"
    past_due = "past_due"
    cancelled = "cancelled"
    expired = "expired"
    paused = "paused"
    trialing = "trialing"


class Subscription(Base):
    """
    Active subscription tracking.
    
    Manages user subscription lifecycle for premium features.
    
    Webhook integration TODO:
    - LemonSqueezy: `subscription_created`, `subscription_updated`, `subscription_cancelled`
    - Coinbase Commerce: Map charge events to subscription periods
    """
    
    __tablename__ = "subscriptions"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # User reference
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="subscriptions")
    
    # Subscription plan
    plan = Column(String(50), nullable=False, index=True)  # standard, elite
    
    # Provider details
    provider = Column(String(50), nullable=False, index=True)  # lemonsqueezy, coinbase_commerce
    provider_subscription_id = Column(String(255), nullable=True, unique=True, index=True)
    provider_customer_id = Column(String(255), nullable=True, index=True)
    
    # Status
    status = Column(String(20), default=SubscriptionStatus.active.value, nullable=False, index=True)
    
    # Billing cycle
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Cancellation tracking
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    cancellation_reason = Column(String(255), nullable=True)
    
    # Lifetime subscription flag (for crypto one-time payments)
    is_lifetime = Column(Boolean, default=False, nullable=False)
    
    # Provider metadata
    provider_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes for analytics
    __table_args__ = (
        Index("idx_subscriptions_user_status", "user_id", "status"),
        Index("idx_subscriptions_status_date", "status", "created_at"),
        Index("idx_subscriptions_plan", "plan", "status"),
        Index("idx_subscriptions_period_end", "current_period_end"),
    )
    
    def __repr__(self):
        return f"<Subscription(user={self.user_id}, plan={self.plan}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        return self.status in (SubscriptionStatus.active.value, SubscriptionStatus.trialing.value)
    
    @property
    def is_churned(self) -> bool:
        """Check if user has churned"""
        return self.status in (SubscriptionStatus.cancelled.value, SubscriptionStatus.expired.value)

