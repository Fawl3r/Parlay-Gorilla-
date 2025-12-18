"""
AffiliateReferral model for tracking referred user signups.

Records when a new user signs up through an affiliate's referral link,
establishing the relationship between affiliate and referred user.
"""

from sqlalchemy import Column, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class AffiliateReferral(Base):
    """
    Tracks referred user signups.
    
    Created when a new user signs up with an affiliate referral code
    (from cookie or URL parameter).
    
    This establishes the permanent relationship between affiliate
    and referred user for commission attribution.
    """
    
    __tablename__ = "affiliate_referrals"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Affiliate reference
    affiliate_id = Column(GUID(), ForeignKey("affiliates.id"), nullable=False, index=True)
    affiliate = relationship("Affiliate", back_populates="referrals")
    
    # Referred user reference
    referred_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    referred_user = relationship("User", back_populates="referral_record", foreign_keys=[referred_user_id])
    
    # Click that led to this referral (optional, for attribution tracking)
    click_id = Column(GUID(), ForeignKey("affiliate_clicks.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_affiliate_referrals_affiliate_id", "affiliate_id"),
        Index("idx_affiliate_referrals_referred_user_id", "referred_user_id"),
        Index("idx_affiliate_referrals_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<AffiliateReferral(id={self.id}, affiliate_id={self.affiliate_id}, referred_user_id={self.referred_user_id})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "affiliate_id": str(self.affiliate_id),
            "referred_user_id": str(self.referred_user_id),
            "click_id": str(self.click_id) if self.click_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }




