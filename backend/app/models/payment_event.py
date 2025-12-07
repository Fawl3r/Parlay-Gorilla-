"""
Payment Event model for storing webhook payloads and payment events.

Stores raw webhook data from LemonSqueezy and Coinbase Commerce
for auditing, debugging, and reconciliation purposes.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class PaymentEvent(Base):
    """
    Payment event log for webhook payloads.
    
    Stores every webhook event received from payment providers.
    This is critical for:
    - Auditing and compliance
    - Debugging payment issues
    - Reconciliation with provider dashboards
    - Replaying events if processing failed
    
    Events from LemonSqueezy:
    - subscription_created
    - subscription_updated
    - subscription_cancelled
    - subscription_payment_success
    - subscription_payment_failed
    - order_created
    
    Events from Coinbase Commerce:
    - charge:created
    - charge:confirmed
    - charge:failed
    - charge:pending
    """
    
    __tablename__ = "payment_events"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # User reference (nullable - may not know user at webhook receipt time)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True, index=True)
    
    # Provider info
    provider = Column(String(20), nullable=False, index=True)  # lemonsqueezy, coinbase
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)  # e.g., "subscription_created"
    event_id = Column(String(255), nullable=True, unique=True, index=True)  # Provider's event ID (for idempotency)
    
    # Raw webhook payload (full JSON for debugging)
    raw_payload = Column(JSONB, nullable=False)
    
    # Extracted key fields for querying
    provider_customer_id = Column(String(255), nullable=True, index=True)
    provider_subscription_id = Column(String(255), nullable=True, index=True)
    provider_order_id = Column(String(255), nullable=True, index=True)
    
    # Processing status
    processed = Column(String(20), default="pending", nullable=False)  # pending, processed, failed, skipped
    processing_error = Column(Text, nullable=True)  # Error message if processing failed
    
    # Timestamps
    occurred_at = Column(DateTime(timezone=True), nullable=True)  # When event occurred (from provider)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_payment_events_provider_type", "provider", "event_type"),
        Index("idx_payment_events_provider_customer", "provider", "provider_customer_id"),
        Index("idx_payment_events_processed", "processed", "created_at"),
    )
    
    def __repr__(self):
        return f"<PaymentEvent(provider={self.provider}, type={self.event_type}, user={self.user_id})>"
    
    def mark_processed(self) -> None:
        """Mark event as successfully processed"""
        from datetime import datetime, timezone
        self.processed = "processed"
        self.processed_at = datetime.now(timezone.utc)
        self.processing_error = None
    
    def mark_failed(self, error: str) -> None:
        """Mark event as failed with error message"""
        from datetime import datetime, timezone
        self.processed = "failed"
        self.processed_at = datetime.now(timezone.utc)
        self.processing_error = error
    
    def mark_skipped(self, reason: str) -> None:
        """Mark event as skipped (e.g., duplicate or irrelevant)"""
        from datetime import datetime, timezone
        self.processed = "skipped"
        self.processed_at = datetime.now(timezone.utc)
        self.processing_error = reason
    
    @classmethod
    def from_webhook(
        cls,
        provider: str,
        event_type: str,
        payload: dict,
        event_id: str = None,
        user_id: str = None,
    ) -> "PaymentEvent":
        """Create a PaymentEvent from webhook data"""
        from datetime import datetime, timezone
        
        return cls(
            id=uuid.uuid4(),
            provider=provider,
            event_type=event_type,
            event_id=event_id,
            raw_payload=payload,
            user_id=uuid.UUID(user_id) if user_id else None,
            occurred_at=datetime.now(timezone.utc),
        )

