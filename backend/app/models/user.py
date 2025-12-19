"""User model for authentication and profiles"""

from sqlalchemy import Column, String, DateTime, Index, JSON, Boolean, Enum, Text, Integer, Numeric, Date, ForeignKey, event
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date, datetime, timezone as tz
from decimal import Decimal
import uuid
import enum
import secrets

from app.database.session import Base
from app.database.types import GUID
from app.utils.datetime_utils import coerce_utc


def _generate_account_number() -> str:
    """
    ORM-level default for account numbers.

    This is a best-effort fallback for code paths that create `User()` directly
    instead of going through `auth_service.create_user()`.
    """
    # 20 hex characters, matches String(20).
    return secrets.token_hex(10)


class UserRole(str, enum.Enum):
    """User role enumeration"""
    user = "user"
    mod = "mod"
    admin = "admin"


class UserPlan(str, enum.Enum):
    """User subscription plan enumeration"""
    free = "free"
    standard = "standard"
    elite = "elite"


class SubscriptionStatusEnum(str, enum.Enum):
    """User subscription status enumeration"""
    none = "none"
    active = "active"
    canceled = "canceled"
    expired = "expired"


class User(Base):
    """User model for storing user profiles and preferences"""
    
    __tablename__ = "users"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, unique=True, index=True)
    # Non-PII stable account number used for on-chain proofs / inscriptions.
    # Format: 20-char hex string. Generated at account creation.
    account_number = Column(String(20), nullable=False, unique=True, index=True, default=_generate_account_number)
    username = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)  # For JWT-based auth
    
    # Role and access control
    role = Column(String, default=UserRole.user.value, nullable=False)
    plan = Column(String, default=UserPlan.free.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Email verification and profile completion status
    email_verified = Column(Boolean, default=False, nullable=False)
    profile_completed = Column(Boolean, default=False, nullable=False)
    
    # ==========================================================================
    # FREE TIER / TRIAL ACCESS
    # ==========================================================================
    # Every new user gets 2 free parlay generations (lifetime, not daily)
    free_parlays_total = Column(Integer, default=2, nullable=False)
    free_parlays_used = Column(Integer, default=0, nullable=False)
    
    # ==========================================================================
    # SUBSCRIPTION STATUS
    # ==========================================================================
    subscription_plan = Column(String(50), nullable=True)  # starter_monthly, elite_monthly, elite_yearly
    subscription_status = Column(String(20), default=SubscriptionStatusEnum.none.value, nullable=False)
    subscription_renewal_date = Column(DateTime(timezone=True), nullable=True)
    subscription_last_billed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Daily parlay usage tracking for subscription limits
    daily_parlays_used = Column(Integer, default=0, nullable=False)
    daily_parlays_usage_date = Column(Date, nullable=True)  # Date of last usage entry, for daily reset
    
    # Premium AI parlay tracking (monthly, resets every 30 days)
    premium_ai_parlays_used = Column(Integer, default=0, nullable=False)
    premium_ai_parlays_period_start = Column(DateTime(timezone=True), nullable=True)  # When current period started
    
    # ==========================================================================
    # CREDIT BALANCE (Per-use purchases)
    # ==========================================================================
    credit_balance = Column(Integer, default=0, nullable=False)
    
    # ==========================================================================
    # AFFILIATE PROGRAM
    # ==========================================================================
    # FK to Affiliate if user is an affiliate (one-to-one via affiliate_account relationship)
    affiliate_id = Column(GUID(), nullable=True, index=True)
    
    # FK to Affiliate who referred this user
    referred_by_affiliate_id = Column(GUID(), ForeignKey("affiliates.id"), nullable=True, index=True)
    
    # User preferences
    default_risk_profile = Column(String, default="balanced")  # conservative, balanced, degen
    favorite_teams = Column(JSON, default=list)  # List of favorite team names
    favorite_sports = Column(JSON, default=list)  # List of favorite sports
    
    # Profile
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)  # User bio/description
    timezone = Column(String(50), nullable=True)  # User's timezone (e.g., "America/New_York")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    parlays = relationship("Parlay", back_populates="user", lazy="dynamic")
    payments = relationship("Payment", back_populates="user", lazy="dynamic")
    subscriptions = relationship("Subscription", back_populates="user", lazy="dynamic")
    admin_sessions = relationship("AdminSession", back_populates="admin", lazy="dynamic")
    badges = relationship("UserBadge", back_populates="user", lazy="dynamic")
    parlay_purchases = relationship("ParlayPurchase", back_populates="user", lazy="dynamic")
    credit_pack_purchases = relationship("CreditPackPurchase", back_populates="user", lazy="dynamic")
    
    # Affiliate relationships
    affiliate_account = relationship(
        "Affiliate",
        back_populates="user",
        foreign_keys="Affiliate.user_id",
        uselist=False,
        lazy="joined"
    )
    referred_by_affiliate = relationship(
        "Affiliate",
        foreign_keys=[referred_by_affiliate_id],
        lazy="joined"
    )
    referral_record = relationship(
        "AffiliateReferral",
        back_populates="referred_user",
        foreign_keys="AffiliateReferral.referred_user_id",
        uselist=False,
        lazy="joined"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_account_number", "account_number"),
        Index("idx_user_role", "role"),
        Index("idx_user_plan", "plan"),
        Index("idx_user_is_active", "is_active"),
        Index("idx_user_email_verified", "email_verified"),
        Index("idx_user_profile_completed", "profile_completed"),
        Index("idx_user_subscription_status", "subscription_status"),
        Index("idx_user_referred_by", "referred_by_affiliate_id"),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.admin.value
    
    @property
    def is_mod(self) -> bool:
        """Check if user has mod or admin role"""
        return self.role in (UserRole.mod.value, UserRole.admin.value)
    
    @property
    def is_premium(self) -> bool:
        """Check if user has a paid plan"""
        return self.plan in (UserPlan.standard.value, UserPlan.elite.value)
    
    # ==========================================================================
    # FREE PARLAY METHODS
    # ==========================================================================
    
    @property
    def has_free_parlays_remaining(self) -> bool:
        """Check if user has free parlays remaining"""
        return self.free_parlays_used < self.free_parlays_total
    
    @property
    def free_parlays_remaining(self) -> int:
        """Get number of free parlays remaining"""
        return max(0, self.free_parlays_total - self.free_parlays_used)
    
    def use_free_parlay(self) -> bool:
        """Use a free parlay. Returns True if successful."""
        if self.has_free_parlays_remaining:
            self.free_parlays_used += 1
            return True
        return False
    
    # ==========================================================================
    # SUBSCRIPTION METHODS
    # ==========================================================================
    
    @property
    def has_active_subscription(self) -> bool:
        """Check if user has an active subscription"""
        # Important: subscriptions can be "canceled" while still valid until the end
        # of the current billing period (grace period). We treat those as active for
        # access purposes until `subscription_renewal_date`.
        status = self.subscription_status
        now = datetime.now(tz.utc)

        if status == SubscriptionStatusEnum.active.value:
            if self.subscription_renewal_date:
                return coerce_utc(self.subscription_renewal_date) > now
            return True

        if status == SubscriptionStatusEnum.canceled.value:
            if self.subscription_renewal_date:
                return coerce_utc(self.subscription_renewal_date) > now
            return False

        return False
    
    def get_subscription_daily_limit(self) -> int:
        """Get the daily parlay limit for user's subscription plan"""
        from app.core.billing_config import get_subscription_plan
        if not self.subscription_plan:
            return 0
        plan = get_subscription_plan(self.subscription_plan)
        return plan.daily_parlay_limit if plan else 0
    
    @property
    def is_within_daily_subscription_limit(self) -> bool:
        """Check if user is within their daily subscription parlay limit"""
        if not self.has_active_subscription:
            return False
        
        # Reset daily counter if it's a new day
        today = date.today()
        if self.daily_parlays_usage_date != today:
            return True  # New day, definitely within limit
        
        daily_limit = self.get_subscription_daily_limit()
        return self.daily_parlays_used < daily_limit
    
    def use_subscription_parlay(self) -> bool:
        """Use a subscription parlay. Returns True if successful."""
        if not self.has_active_subscription:
            return False
        
        today = date.today()
        
        # Reset counter if new day
        if self.daily_parlays_usage_date != today:
            self.daily_parlays_used = 0
            self.daily_parlays_usage_date = today
        
        daily_limit = self.get_subscription_daily_limit()
        if self.daily_parlays_used < daily_limit:
            self.daily_parlays_used += 1
            return True
        return False
    
    @property
    def subscription_parlays_remaining_today(self) -> int:
        """Get number of subscription parlays remaining today"""
        if not self.has_active_subscription:
            return 0
        
        today = date.today()
        if self.daily_parlays_usage_date != today:
            return self.get_subscription_daily_limit()
        
        daily_limit = self.get_subscription_daily_limit()
        return max(0, daily_limit - self.daily_parlays_used)
    
    # ==========================================================================
    # CREDIT METHODS
    # ==========================================================================
    
    def has_credits(self, amount: int) -> bool:
        """Check if user has at least the specified amount of credits"""
        return self.credit_balance >= amount
    
    def use_credits(self, amount: int) -> bool:
        """Deduct credits from balance. Returns True if successful."""
        if self.has_credits(amount):
            self.credit_balance -= amount
            return True
        return False
    
    def add_credits(self, amount: int) -> None:
        """Add credits to balance"""
        self.credit_balance += amount
    
    # ==========================================================================
    # AFFILIATE METHODS
    # ==========================================================================
    
    @property
    def is_affiliate(self) -> bool:
        """Check if user is an affiliate"""
        return self.affiliate_account is not None
    
    @property
    def was_referred(self) -> bool:
        """Check if user was referred by an affiliate"""
        return self.referred_by_affiliate_id is not None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "email": self.email,
            "account_number": self.account_number,
            "username": self.username,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "role": self.role,
            "plan": self.plan,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "profile_completed": self.profile_completed,
            "free_parlays_remaining": self.free_parlays_remaining,
            "credit_balance": self.credit_balance,
            "subscription_plan": self.subscription_plan,
            "subscription_status": self.subscription_status,
            "has_active_subscription": self.has_active_subscription,
            "is_affiliate": self.is_affiliate,
            "was_referred": self.was_referred,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@event.listens_for(User, "before_insert")
def _user_before_insert(_mapper, _connection, target: User) -> None:
    # Guarantee a non-null account number even if a caller explicitly sets it to None.
    if not getattr(target, "account_number", None):
        target.account_number = _generate_account_number()

