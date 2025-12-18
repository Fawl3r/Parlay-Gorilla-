"""
Affiliate model for the affiliate program.

Tracks affiliate accounts linked to users, including:
- Referral code and URL
- Tier and commission rates
- Total referred revenue and commissions earned
"""

from sqlalchemy import Column, String, DateTime, Index, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
import uuid
import secrets
import string

from app.database.session import Base
from app.database.types import GUID
from app.core.billing_config import AffiliateTier, AFFILIATE_TIERS, calculate_tier_for_revenue


def generate_referral_code(length: int = 8) -> str:
    """Generate a unique referral code"""
    chars = string.ascii_uppercase + string.digits
    # Remove confusing characters
    chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '').replace('L', '')
    return ''.join(secrets.choice(chars) for _ in range(length))


class Affiliate(Base):
    """
    Affiliate account for referral program.
    
    Each affiliate has a unique referral code and earns commissions
    on referred user purchases (subscriptions and credit packs).
    
    Commission rates are based on tier, which upgrades automatically
    as total_referred_revenue increases.
    """
    
    __tablename__ = "affiliates"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # User reference (affiliate must be a registered user)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Referral tracking
    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    
    # Tier and commission rates (stored for quick access, updated when tier changes)
    tier = Column(String(20), default=AffiliateTier.ROOKIE.value, nullable=False, index=True)
    commission_rate_sub_first = Column(Numeric(5, 4), default=Decimal("0.20"), nullable=False)
    commission_rate_sub_recurring = Column(Numeric(5, 4), default=Decimal("0.00"), nullable=False)
    commission_rate_credits = Column(Numeric(5, 4), default=Decimal("0.20"), nullable=False)
    
    # Totals (updated on each sale)
    total_referred_revenue = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_commission_earned = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_commission_paid = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    
    # Stats
    total_clicks = Column(Numeric(10, 0), default=0, nullable=False)
    total_referrals = Column(Numeric(10, 0), default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_approved = Column(Boolean, default=True, nullable=False)  # For manual approval if needed
    
    # Payment info (for payouts)
    payout_email = Column(String(255), nullable=True)  # PayPal or crypto address
    payout_method = Column(String(50), nullable=True)  # paypal, crypto, bank
    
    # Tax information (required for US affiliates earning $600+ per year)
    # W-9 form fields (US affiliates)
    tax_form_type = Column(String(20), nullable=True)  # w9, w8ben, none
    tax_form_status = Column(String(20), default="not_submitted", nullable=False)  # not_submitted, submitted, verified, rejected
    tax_form_submitted_at = Column(DateTime(timezone=True), nullable=True)
    tax_form_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Legal/Business Information
    legal_name = Column(String(255), nullable=True)  # Full legal name for tax forms
    business_name = Column(String(255), nullable=True)  # Business name if different from legal name
    tax_classification = Column(String(50), nullable=True)  # Individual, Partnership, C-Corp, S-Corp, LLC, etc.
    
    # Address (for tax forms)
    tax_address_street = Column(String(255), nullable=True)
    tax_address_city = Column(String(100), nullable=True)
    tax_address_state = Column(String(50), nullable=True)  # State/Province
    tax_address_zip = Column(String(20), nullable=True)  # ZIP/Postal code
    tax_address_country = Column(String(100), nullable=True, default="US")  # Country code
    
    # Tax ID numbers
    tax_id_number = Column(String(50), nullable=True)  # SSN (masked) or EIN for US, foreign tax ID for international
    tax_id_type = Column(String(20), nullable=True)  # ssn, ein, foreign_tax_id
    
    # International tax (W-8BEN)
    country_of_residence = Column(String(100), nullable=True)  # For W-8BEN
    foreign_tax_id = Column(String(50), nullable=True)  # Foreign tax identification number
    
    # Tax form signature
    tax_form_signed_at = Column(DateTime(timezone=True), nullable=True)
    tax_form_ip_address = Column(String(45), nullable=True)  # IP address when form was signed
    
    # Minimum payout threshold before requiring tax forms (default $600 for US)
    tax_form_required_threshold = Column(Numeric(10, 2), default=Decimal("600.00"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="affiliate_account", foreign_keys=[user_id])
    clicks = relationship("AffiliateClick", back_populates="affiliate", lazy="dynamic")
    referrals = relationship("AffiliateReferral", back_populates="affiliate", lazy="dynamic")
    commissions = relationship("AffiliateCommission", back_populates="affiliate", lazy="dynamic")
    payouts = relationship("AffiliatePayout", back_populates="affiliate", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index("idx_affiliates_user_id", "user_id"),
        Index("idx_affiliates_referral_code", "referral_code"),
        Index("idx_affiliates_tier", "tier"),
        Index("idx_affiliates_is_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<Affiliate(id={self.id}, code={self.referral_code}, tier={self.tier})>"
    
    @classmethod
    def create_with_referral_code(cls, user_id: uuid.UUID) -> "Affiliate":
        """Create a new affiliate with a unique referral code"""
        return cls(
            id=uuid.uuid4(),
            user_id=user_id,
            referral_code=generate_referral_code(),
            tier=AffiliateTier.ROOKIE.value,
            commission_rate_sub_first=Decimal("0.20"),
            commission_rate_sub_recurring=Decimal("0.00"),
            commission_rate_credits=Decimal("0.20"),
        )
    
    @property
    def referral_url(self) -> str:
        """Generate the full referral URL"""
        from app.core.config import settings
        return f"{settings.frontend_url}?ref={self.referral_code}"
    
    @property
    def pending_commission(self) -> Decimal:
        """Calculate pending commission (earned but not yet paid)"""
        return self.total_commission_earned - self.total_commission_paid
    
    @property
    def requires_tax_form(self) -> bool:
        """Check if tax form is required based on earnings threshold"""
        return float(self.total_commission_earned) >= float(self.tax_form_required_threshold)
    
    @property
    def tax_form_complete(self) -> bool:
        """Check if tax form has been submitted and verified"""
        return self.tax_form_status == "verified"
    
    def mask_tax_id(self) -> str:
        """Return masked tax ID for display (e.g., XXX-XX-1234)"""
        if not self.tax_id_number:
            return None
        if self.tax_id_type == "ssn" and len(self.tax_id_number) >= 4:
            return f"XXX-XX-{self.tax_id_number[-4:]}"
        elif self.tax_id_type == "ein" and len(self.tax_id_number) >= 4:
            return f"XX-{self.tax_id_number[-4:]}"
        return "XXX-XX-XXXX"  # Default mask
    
    def recalculate_tier(self) -> bool:
        """
        Recalculate and update tier based on total_referred_revenue.
        Returns True if tier was upgraded.
        """
        new_tier_config = calculate_tier_for_revenue(self.total_referred_revenue)
        old_tier = self.tier
        
        if new_tier_config.tier.value != self.tier:
            self.tier = new_tier_config.tier.value
            self.commission_rate_sub_first = new_tier_config.commission_rate_sub_first
            self.commission_rate_sub_recurring = new_tier_config.commission_rate_sub_recurring
            self.commission_rate_credits = new_tier_config.commission_rate_credits
            return old_tier != self.tier
        
        return False
    
    def add_revenue(self, amount: Decimal, commission: Decimal) -> None:
        """Add revenue and commission from a sale"""
        self.total_referred_revenue += amount
        self.total_commission_earned += commission
    
    def increment_click(self) -> None:
        """Increment click counter"""
        self.total_clicks += 1
    
    def increment_referral(self) -> None:
        """Increment referral counter"""
        self.total_referrals += 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "referral_code": self.referral_code,
            "referral_url": self.referral_url,
            "tier": self.tier,
            "commission_rates": {
                "subscription_first": float(self.commission_rate_sub_first),
                "subscription_recurring": float(self.commission_rate_sub_recurring),
                "credits": float(self.commission_rate_credits),
            },
            "stats": {
                "total_clicks": int(self.total_clicks),
                "total_referrals": int(self.total_referrals),
                "total_referred_revenue": float(self.total_referred_revenue),
                "total_commission_earned": float(self.total_commission_earned),
                "total_commission_paid": float(self.total_commission_paid),
                "pending_commission": float(self.pending_commission),
            },
            "is_active": self.is_active,
            "payout_email": self.payout_email,
            "payout_method": self.payout_method,
            "tax_info": {
                "form_type": self.tax_form_type,
                "form_status": self.tax_form_status,
                "requires_form": self.requires_tax_form,
                "form_complete": self.tax_form_complete,
                "submitted_at": self.tax_form_submitted_at.isoformat() if self.tax_form_submitted_at else None,
                "verified_at": self.tax_form_verified_at.isoformat() if self.tax_form_verified_at else None,
                "threshold": float(self.tax_form_required_threshold),
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def to_public_dict(self) -> dict:
        """Public info for display to referred users"""
        return {
            "referral_code": self.referral_code,
            "tier": self.tier,
        }

