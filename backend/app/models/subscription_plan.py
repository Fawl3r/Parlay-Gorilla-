"""
Subscription Plan model for storing available plans.

Stores plan metadata including pricing, billing cycle, and provider product IDs
for LemonSqueezy and Coinbase Commerce integration.
"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.sql import func
import uuid
import enum

from app.database.session import Base
from app.database.types import GUID


class BillingCycle(str, enum.Enum):
    """Billing cycle enumeration"""
    monthly = "monthly"
    annual = "annual"
    lifetime = "lifetime"
    one_time = "one_time"  # For pay-per-use purchases (single parlay)


class PaymentProvider(str, enum.Enum):
    """Payment provider enumeration"""
    lemonsqueezy = "lemonsqueezy"
    coinbase = "coinbase"
    stripe = "stripe"


class SubscriptionPlan(Base):
    """
    Subscription plan definitions.
    
    Stores all available subscription plans with their pricing,
    features, and payment provider product IDs.
    
    Example plans:
    - PG_FREE: Free tier (no payment required)
    - PG_PREMIUM_MONTHLY: Monthly premium via LemonSqueezy
    - PG_PREMIUM_ANNUAL: Annual premium via LemonSqueezy
    - PG_LIFETIME: Lifetime access via Coinbase Commerce (crypto)
    """
    
    __tablename__ = "subscription_plans"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Plan identification
    code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "PG_PREMIUM_MONTHLY"
    name = Column(String(100), nullable=False)  # e.g., "Gorilla Premium"
    description = Column(Text, nullable=True)  # Rich description for UI
    
    # Pricing (display only - actual prices managed by providers)
    price_cents = Column(Integer, nullable=False, default=0)  # Price in cents (e.g., 999 = $9.99)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Billing configuration
    billing_cycle = Column(String(20), nullable=False, default=BillingCycle.monthly.value)
    
    # Provider configuration
    provider = Column(String(20), nullable=False, index=True)  # lemonsqueezy or coinbase
    provider_product_id = Column(String(255), nullable=True)  # LemonSqueezy product/variant ID
    provider_price_id = Column(String(255), nullable=True)  # For providers that use separate price IDs
    
    # Plan status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False)  # Highlight on pricing page
    
    # Feature flags for this plan (JSON-like approach via individual columns)
    max_ai_parlays_per_day = Column(Integer, default=1)  # -1 for unlimited
    can_use_custom_builder = Column(Boolean, default=False)
    can_use_upset_finder = Column(Boolean, default=False)
    can_use_multi_sport = Column(Boolean, default=False)
    can_save_parlays = Column(Boolean, default=False)
    ad_free = Column(Boolean, default=False)
    
    # Display order for pricing page
    display_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SubscriptionPlan(code={self.code}, name={self.name}, provider={self.provider})>"
    
    @property
    def price_dollars(self) -> float:
        """Get price in dollars"""
        return self.price_cents / 100
    
    @property
    def is_free(self) -> bool:
        """Check if this is a free plan"""
        return self.price_cents == 0
    
    @property
    def is_lifetime(self) -> bool:
        """Check if this is a lifetime plan"""
        return self.billing_cycle == BillingCycle.lifetime.value
    
    @property
    def is_one_time(self) -> bool:
        """Check if this is a one-time purchase (pay-per-use)"""
        return self.billing_cycle == BillingCycle.one_time.value
    
    @property
    def has_unlimited_parlays(self) -> bool:
        """Check if plan has unlimited AI parlays"""
        return self.max_ai_parlays_per_day == -1
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "price_cents": self.price_cents,
            "price_dollars": self.price_dollars,
            "currency": self.currency,
            "billing_cycle": self.billing_cycle,
            "provider": self.provider,
            "is_active": self.is_active,
            "is_featured": self.is_featured,
            "is_free": self.is_free,
            "is_lifetime": self.is_lifetime,
            "is_one_time": self.is_one_time,
            "features": {
                "max_ai_parlays_per_day": self.max_ai_parlays_per_day,
                "unlimited_ai_parlays": self.has_unlimited_parlays,
                "custom_builder": self.can_use_custom_builder,
                "upset_finder": self.can_use_upset_finder,
                "multi_sport": self.can_use_multi_sport,
                "save_parlays": self.can_save_parlays,
                "ad_free": self.ad_free,
            },
        }

