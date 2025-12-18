"""
Parlay Purchase Service for managing one-time parlay purchases.

Handles the pay-per-use model for free users who have exhausted
their daily free parlays.

Pricing:
- $3 for single-sport parlay
- $5 for multi-sport parlay

Purchases expire after 24 hours if unused.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import uuid
import logging

from app.models.parlay_purchase import ParlayPurchase, ParlayType, PurchaseStatus
from app.models.payment import Payment, PaymentStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class ParlayPurchaseService:
    """
    Service for managing one-time parlay purchases.
    
    Primary use cases:
    1. Create purchase record: create_parlay_purchase()
    2. Get available purchase: get_unused_purchase()
    3. Mark as used: mark_purchase_used()
    4. Check availability: has_unused_purchase()
    5. Cleanup expired: cleanup_expired_purchases()
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_parlay_purchase(
        self,
        user_id: str,
        parlay_type: str,
        provider: str,
        provider_checkout_id: Optional[str] = None,
    ) -> ParlayPurchase:
        """
        Create a new parlay purchase record.
        
        Called when a checkout session is initiated.
        Status starts as 'pending' until payment is confirmed.
        
        Args:
            user_id: UUID of the user
            parlay_type: 'single' or 'multi'
            provider: Payment provider ('lemonsqueezy' or 'coinbase')
            provider_checkout_id: External checkout session ID
            
        Returns:
            New ParlayPurchase record
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            raise ValueError(f"Invalid user_id: {user_id}")
        
        # Determine price based on parlay type
        if parlay_type == ParlayType.single.value:
            amount = Decimal(str(settings.single_parlay_price_dollars))
        elif parlay_type == ParlayType.multi.value:
            amount = Decimal(str(settings.multi_parlay_price_dollars))
        else:
            raise ValueError(f"Invalid parlay_type: {parlay_type}")
        
        purchase = ParlayPurchase(
            id=uuid.uuid4(),
            user_id=user_uuid,
            parlay_type=parlay_type,
            amount=amount,
            currency="USD",
            status=PurchaseStatus.pending.value,
            provider=provider,
            provider_checkout_id=provider_checkout_id,
        )
        
        self.db.add(purchase)
        await self.db.commit()
        await self.db.refresh(purchase)
        
        logger.info(f"Created parlay purchase {purchase.id} for user {user_id}, type={parlay_type}, amount=${amount}")
        
        return purchase
    
    async def confirm_purchase(
        self,
        purchase_id: str,
        payment_id: Optional[str] = None,
    ) -> ParlayPurchase:
        """
        Confirm a parlay purchase after successful payment.
        
        Sets status to 'available' and sets expiry time.
        
        Args:
            purchase_id: UUID of the purchase
            payment_id: UUID of the associated payment record (optional)
            
        Returns:
            Updated ParlayPurchase record
        """
        try:
            purchase_uuid = uuid.UUID(purchase_id) if isinstance(purchase_id, str) else purchase_id
        except ValueError:
            raise ValueError(f"Invalid purchase_id: {purchase_id}")
        
        result = await self.db.execute(
            select(ParlayPurchase).where(ParlayPurchase.id == purchase_uuid)
        )
        purchase = result.scalar_one_or_none()
        
        if not purchase:
            raise ValueError(f"Purchase not found: {purchase_id}")
        
        if purchase.status != PurchaseStatus.pending.value:
            logger.warning(f"Purchase {purchase_id} already processed, status={purchase.status}")
            return purchase
        
        # Update purchase status
        purchase.status = PurchaseStatus.available.value
        purchase.expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.parlay_purchase_expiry_hours)
        
        if payment_id:
            try:
                purchase.payment_id = uuid.UUID(payment_id) if isinstance(payment_id, str) else payment_id
            except ValueError:
                logger.warning(f"Invalid payment_id format: {payment_id}")
        
        await self.db.commit()
        await self.db.refresh(purchase)
        
        logger.info(f"Confirmed parlay purchase {purchase_id}, expires at {purchase.expires_at}")
        
        return purchase
    
    async def get_purchase_by_checkout_id(self, provider_checkout_id: str) -> Optional[ParlayPurchase]:
        """
        Get a purchase by its provider checkout ID.
        
        Used during webhook processing to find the associated purchase.
        """
        result = await self.db.execute(
            select(ParlayPurchase).where(
                ParlayPurchase.provider_checkout_id == provider_checkout_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_unused_purchase(
        self,
        user_id: str,
        parlay_type: Optional[str] = None,
    ) -> Optional[ParlayPurchase]:
        """
        Get an unused (available) parlay purchase for the user.
        
        Args:
            user_id: UUID of the user
            parlay_type: Optional filter by type ('single' or 'multi')
                        If None, returns any available purchase (preferring multi for flexibility)
            
        Returns:
            Available ParlayPurchase or None
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            return None
        
        now = datetime.now(timezone.utc)
        
        # Build query
        conditions = [
            ParlayPurchase.user_id == user_uuid,
            ParlayPurchase.status == PurchaseStatus.available.value,
            or_(
                ParlayPurchase.expires_at.is_(None),
                ParlayPurchase.expires_at > now
            )
        ]
        
        if parlay_type:
            conditions.append(ParlayPurchase.parlay_type == parlay_type)
        
        result = await self.db.execute(
            select(ParlayPurchase).where(
                and_(*conditions)
            ).order_by(
                # Prefer multi-sport purchases for flexibility (they can be used for single too)
                ParlayPurchase.parlay_type.desc(),
                ParlayPurchase.created_at.asc()  # FIFO within type
            ).limit(1)
        )
        
        return result.scalar_one_or_none()
    
    async def has_unused_purchase(
        self,
        user_id: str,
        is_multi_sport: bool = False,
    ) -> bool:
        """
        Check if user has an available parlay purchase.
        
        For multi-sport requests, only multi purchases are valid.
        For single-sport requests, either single or multi purchases are valid.
        
        Args:
            user_id: UUID of the user
            is_multi_sport: True if the parlay request is multi-sport
            
        Returns:
            True if user has valid purchase
        """
        if is_multi_sport:
            # Multi-sport requests require multi purchase
            purchase = await self.get_unused_purchase(user_id, ParlayType.multi.value)
        else:
            # Single-sport can use either type (multi is more flexible)
            purchase = await self.get_unused_purchase(user_id)
        
        return purchase is not None
    
    async def mark_purchase_used(
        self,
        user_id: str,
        is_multi_sport: bool = False,
        parlay_id: Optional[str] = None,
    ) -> Optional[ParlayPurchase]:
        """
        Mark a purchase as used after parlay generation.
        
        Should be called AFTER successfully generating a parlay.
        
        Args:
            user_id: UUID of the user
            is_multi_sport: True if multi-sport parlay was generated
            parlay_id: Optional UUID of the generated parlay
            
        Returns:
            Updated ParlayPurchase or None if no purchase was available
        """
        if is_multi_sport:
            purchase = await self.get_unused_purchase(user_id, ParlayType.multi.value)
        else:
            purchase = await self.get_unused_purchase(user_id)
        
        if not purchase:
            logger.warning(f"No available purchase found for user {user_id}")
            return None
        
        # Mark as used
        purchase.status = PurchaseStatus.used.value
        purchase.used_at = datetime.now(timezone.utc)
        
        if parlay_id:
            try:
                purchase.parlay_id = uuid.UUID(parlay_id) if isinstance(parlay_id, str) else parlay_id
            except ValueError:
                logger.warning(f"Invalid parlay_id format: {parlay_id}")
        
        await self.db.commit()
        await self.db.refresh(purchase)
        
        logger.info(f"Marked purchase {purchase.id} as used for user {user_id}")
        
        return purchase
    
    async def get_user_purchases(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ParlayPurchase]:
        """
        Get user's parlay purchase history.
        
        Args:
            user_id: UUID of the user
            status: Optional filter by status
            limit: Maximum number of records to return
            
        Returns:
            List of ParlayPurchase records
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            return []
        
        conditions = [ParlayPurchase.user_id == user_uuid]
        
        if status:
            conditions.append(ParlayPurchase.status == status)
        
        result = await self.db.execute(
            select(ParlayPurchase).where(
                and_(*conditions)
            ).order_by(
                ParlayPurchase.created_at.desc()
            ).limit(limit)
        )
        
        return list(result.scalars().all())
    
    async def cleanup_expired_purchases(self) -> int:
        """
        Mark expired purchases as expired.
        
        Should be called periodically (e.g., via cron job).
        
        Returns:
            Number of purchases marked as expired
        """
        now = datetime.now(timezone.utc)
        
        result = await self.db.execute(
            select(ParlayPurchase).where(
                and_(
                    ParlayPurchase.status == PurchaseStatus.available.value,
                    ParlayPurchase.expires_at.isnot(None),
                    ParlayPurchase.expires_at <= now
                )
            )
        )
        
        expired_purchases = result.scalars().all()
        count = 0
        
        for purchase in expired_purchases:
            purchase.status = PurchaseStatus.expired.value
            count += 1
        
        if count > 0:
            await self.db.commit()
            logger.info(f"Marked {count} parlay purchases as expired")
        
        return count
    
    async def get_purchase_stats(self, user_id: str) -> dict:
        """
        Get purchase statistics for a user.
        
        Returns:
            Dictionary with purchase stats
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            return {"available": 0, "used": 0, "expired": 0, "total_spent": 0}
        
        purchases = await self.get_user_purchases(user_id)
        
        stats = {
            "available": 0,
            "used": 0,
            "expired": 0,
            "pending": 0,
            "total_spent": Decimal("0.00"),
        }
        
        for p in purchases:
            if p.status == PurchaseStatus.available.value and not p.is_expired:
                stats["available"] += 1
            elif p.status == PurchaseStatus.used.value:
                stats["used"] += 1
                stats["total_spent"] += p.amount
            elif p.status == PurchaseStatus.expired.value or p.is_expired:
                stats["expired"] += 1
            elif p.status == PurchaseStatus.pending.value:
                stats["pending"] += 1
        
        stats["total_spent"] = float(stats["total_spent"])
        
        return stats


# Helper function for dependency injection
async def get_parlay_purchase_service(db: AsyncSession) -> ParlayPurchaseService:
    """Get parlay purchase service instance."""
    return ParlayPurchaseService(db)




