"""Affiliate payout model for tracking payout history + tax reporting ledger."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
import uuid
from datetime import datetime, timezone
from enum import Enum

from app.database.session import Base
from app.database.types import GUID


class PayoutStatus(str, Enum):
    """Payout status enumeration"""
    PENDING = "pending"           # Created but not yet processed
    PROCESSING = "processing"     # Currently being processed
    COMPLETED = "completed"       # Successfully paid
    FAILED = "failed"             # Payment failed
    CANCELLED = "cancelled"        # Cancelled before processing


class PayoutMethod(str, Enum):
    """Payout method enumeration"""
    PAYPAL = "paypal"
    CRYPTO = "crypto"
    BANK = "bank"


class AffiliatePayout(Base):
    """
    Tracks affiliate payout batches and individual payouts.
    
    A payout can contain multiple commissions that are paid together.
    This allows for batch processing and better tracking.
    """
    
    __tablename__ = "affiliate_payouts"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Affiliate reference
    affiliate_id = Column(GUID(), ForeignKey("affiliates.id"), nullable=False, index=True)
    affiliate = relationship("Affiliate", back_populates="payouts")
    
    # ------------------------------------------------------------------
    # PAYOUT AMOUNTS (USD)
    # ------------------------------------------------------------------
    # `amount` is the gross program payout amount in USD (sum of commissions).
    #
    # For tax reporting, use `tax_amount_usd` (FMV at payout time). For PayPal
    # it typically equals `amount`; for crypto it is derived from the asset
    # amount and valuation quote at payout time.
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)  # Always USD for tax ledger
    payout_method = Column(String(50), nullable=False, index=True)  # paypal, crypto, bank
    tax_amount_usd = Column(Numeric(12, 2), nullable=True)

    # ------------------------------------------------------------------
    # TAX LEDGER (CRYPTO DETAILS)
    # ------------------------------------------------------------------
    # For crypto payouts, store what was actually sent + valuation inputs.
    asset_symbol = Column(String(12), nullable=True)  # e.g. USDC
    asset_amount = Column(Numeric(18, 6), nullable=True)  # e.g. 100.000000
    asset_chain = Column(String(32), nullable=True)  # e.g. ethereum, polygon, solana
    transaction_hash = Column(String(255), nullable=True)  # blockchain tx hash (if available)

    # USD valuation snapshot at time of payout (IRS audit trail)
    valuation_usd_per_asset = Column(Numeric(18, 8), nullable=True)  # USD per 1 unit of asset
    valuation_source = Column(String(64), nullable=True)  # e.g. coinbase_spot | stablecoin_peg
    valuation_at = Column(DateTime(timezone=True), nullable=True)
    valuation_raw = Column(Text, nullable=True)  # JSON string of quote payload
    
    # Recipient information
    recipient_email = Column(String(255), nullable=False)  # PayPal email or crypto address
    recipient_name = Column(String(255), nullable=True)  # Optional name
    
    # Status tracking
    status = Column(String(20), default=PayoutStatus.PENDING.value, nullable=False, index=True)
    
    # Provider-specific IDs
    provider_payout_id = Column(String(255), nullable=True, index=True)  # PayPal batch ID, crypto tx hash, etc.
    provider_response = Column(Text, nullable=True)  # Full provider response JSON
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)  # Admin notes
    
    # Relationships
    commissions = relationship(
        "AffiliateCommission",
        secondary="affiliate_payout_commissions",
        back_populates="payouts"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_payouts_affiliate_status", "affiliate_id", "status"),
        Index("idx_payouts_status_created", "status", "created_at"),
        Index("idx_payouts_provider_id", "provider_payout_id"),
        Index("idx_payouts_completed_at", "completed_at"),
    )
    
    def __repr__(self):
        return f"<AffiliatePayout(id={self.id}, amount={self.amount}, status={self.status})>"
    
    def mark_processing(self) -> None:
        """Mark payout as processing"""
        self.status = PayoutStatus.PROCESSING.value
        self.processed_at = datetime.now(timezone.utc)
    
    def mark_completed(self, provider_payout_id: str = None, provider_response: str = None) -> None:
        """Mark payout as completed"""
        self.status = PayoutStatus.COMPLETED.value
        self.completed_at = datetime.now(timezone.utc)
        if provider_payout_id:
            self.provider_payout_id = provider_payout_id
        if provider_response:
            self.provider_response = provider_response
    
    def mark_failed(self, error_message: str, error_code: str = None) -> None:
        """Mark payout as failed"""
        self.status = PayoutStatus.FAILED.value
        self.error_message = error_message
        self.error_code = error_code
        self.retry_count += 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "affiliate_id": str(self.affiliate_id),
            "amount": float(self.amount),
            "currency": self.currency,
            "payout_method": self.payout_method,
            "tax_amount_usd": float(self.tax_amount_usd) if self.tax_amount_usd is not None else None,
            "asset_symbol": self.asset_symbol,
            "asset_amount": float(self.asset_amount) if self.asset_amount is not None else None,
            "asset_chain": self.asset_chain,
            "transaction_hash": self.transaction_hash,
            "valuation_usd_per_asset": float(self.valuation_usd_per_asset) if self.valuation_usd_per_asset is not None else None,
            "valuation_source": self.valuation_source,
            "valuation_at": self.valuation_at.isoformat() if self.valuation_at else None,
            "recipient_email": self.recipient_email,
            "recipient_name": self.recipient_name,
            "status": self.status,
            "provider_payout_id": self.provider_payout_id,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "retry_count": int(self.retry_count),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
        }


# Association table for many-to-many relationship between payouts and commissions
from sqlalchemy import Table

affiliate_payout_commissions = Table(
    "affiliate_payout_commissions",
    Base.metadata,
    Column("payout_id", GUID(), ForeignKey("affiliate_payouts.id"), primary_key=True),
    Column("commission_id", GUID(), ForeignKey("affiliate_commissions.id"), primary_key=True),
    Index("idx_payout_commissions_payout", "payout_id"),
    Index("idx_payout_commissions_commission", "commission_id"),
)

