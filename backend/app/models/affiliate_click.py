"""
AffiliateClick model for tracking referral link clicks.

Records each click on an affiliate's referral link for analytics
and attribution purposes.
"""

from sqlalchemy import Column, String, DateTime, Index, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class AffiliateClick(Base):
    """
    Tracks clicks on affiliate referral links.
    
    Used for:
    - Attribution (connecting signups to affiliates)
    - Analytics (conversion rate tracking)
    - Fraud detection (unusual click patterns)
    """
    
    __tablename__ = "affiliate_clicks"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Affiliate reference
    affiliate_id = Column(GUID(), ForeignKey("affiliates.id"), nullable=False, index=True)
    affiliate = relationship("Affiliate", back_populates="clicks")
    
    # Request info
    ip_address = Column(String(45), nullable=True)  # IPv6 can be up to 45 chars
    user_agent = Column(Text, nullable=True)
    referer_url = Column(Text, nullable=True)
    landing_page = Column(Text, nullable=True)
    
    # UTM parameters (if any)
    utm_source = Column(String(255), nullable=True)
    utm_medium = Column(String(255), nullable=True)
    utm_campaign = Column(String(255), nullable=True)
    
    # Conversion tracking
    converted = Column(String(1), default='N', nullable=False)  # Y/N
    converted_user_id = Column(GUID(), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_affiliate_clicks_affiliate_id", "affiliate_id"),
        Index("idx_affiliate_clicks_created_at", "created_at"),
        Index("idx_affiliate_clicks_ip_address", "ip_address"),
        Index("idx_affiliate_clicks_converted", "converted"),
    )
    
    def __repr__(self):
        return f"<AffiliateClick(id={self.id}, affiliate_id={self.affiliate_id})>"
    
    def mark_converted(self, user_id: uuid.UUID) -> None:
        """Mark this click as converted to a signup"""
        self.converted = 'Y'
        self.converted_user_id = user_id
        self.converted_at = func.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "affiliate_id": str(self.affiliate_id),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent[:100] if self.user_agent else None,  # Truncate for display
            "referer_url": self.referer_url,
            "landing_page": self.landing_page,
            "utm_source": self.utm_source,
            "utm_medium": self.utm_medium,
            "utm_campaign": self.utm_campaign,
            "converted": self.converted == 'Y',
            "converted_user_id": str(self.converted_user_id) if self.converted_user_id else None,
            "converted_at": self.converted_at.isoformat() if self.converted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }




