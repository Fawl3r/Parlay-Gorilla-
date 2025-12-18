"""
Payment Service for subscription and payment management.

Stub implementation ready for LemonSqueezy/Coinbase Commerce webhook integration.

TODO: Implement webhook handlers:
- LemonSqueezy: order_created, subscription_payment_success, subscription_cancelled
- Coinbase Commerce: charge:confirmed, charge:failed, charge:pending
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import uuid

from app.models.payment import Payment, PaymentStatus, PaymentProvider
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User, UserPlan


class PaymentService:
    """
    Service for managing payments and subscriptions.
    
    This is a stub implementation. Actual payment processing
    will be handled by LemonSqueezy/Coinbase Commerce webhooks.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==========================================
    # Payment Management
    # ==========================================
    
    async def create_payment(
        self,
        user_id: str,
        amount: float,
        plan: str,
        provider: str,
        currency: str = "USD",
        provider_payment_id: Optional[str] = None,
        provider_order_id: Optional[str] = None,
        provider_metadata: Optional[Dict[str, Any]] = None,
    ) -> Payment:
        """
        Create a new payment record.
        
        Called from webhook handlers when payment is initiated.
        """
        payment = Payment(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            amount=amount,
            currency=currency,
            plan=plan,
            provider=provider,
            provider_payment_id=provider_payment_id,
            provider_order_id=provider_order_id,
            provider_metadata=provider_metadata,
            status=PaymentStatus.pending.value,
        )
        
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        
        return payment
    
    async def mark_payment_paid(
        self,
        payment_id: str,
        provider_payment_id: Optional[str] = None,
    ) -> Optional[Payment]:
        """
        Mark a payment as paid.
        
        Called from webhook handlers when payment is confirmed.
        Also upgrades the user's plan.
        """
        result = await self.db.execute(
            select(Payment).where(Payment.id == uuid.UUID(payment_id))
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            return None
        
        payment.status = PaymentStatus.paid.value
        payment.paid_at = datetime.utcnow()
        if provider_payment_id:
            payment.provider_payment_id = provider_payment_id
        
        # Upgrade user plan
        await self._upgrade_user_plan(str(payment.user_id), payment.plan)
        
        await self.db.commit()
        await self.db.refresh(payment)
        
        return payment
    
    async def mark_payment_failed(
        self,
        payment_id: str,
        error_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Payment]:
        """Mark a payment as failed."""
        result = await self.db.execute(
            select(Payment).where(Payment.id == uuid.UUID(payment_id))
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            return None
        
        payment.status = PaymentStatus.failed.value
        if error_metadata:
            payment.provider_metadata = {
                **(payment.provider_metadata or {}),
                "error": error_metadata,
            }
        
        await self.db.commit()
        await self.db.refresh(payment)
        
        return payment
    
    async def get_payment_by_provider_id(
        self,
        provider: str,
        provider_payment_id: str,
    ) -> Optional[Payment]:
        """Get payment by provider's payment ID."""
        result = await self.db.execute(
            select(Payment).where(
                and_(
                    Payment.provider == provider,
                    Payment.provider_payment_id == provider_payment_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_payments(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[Payment]:
        """Get payment history for a user."""
        result = await self.db.execute(
            select(Payment).where(
                Payment.user_id == uuid.UUID(user_id)
            ).order_by(Payment.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
    
    # ==========================================
    # Subscription Management
    # ==========================================
    
    async def create_subscription(
        self,
        user_id: str,
        plan: str,
        provider: str,
        provider_subscription_id: Optional[str] = None,
        provider_customer_id: Optional[str] = None,
        current_period_end: Optional[datetime] = None,
        provider_metadata: Optional[Dict[str, Any]] = None,
    ) -> Subscription:
        """
        Create a new subscription.
        
        Called from webhook handlers when subscription is created.
        """
        # Cancel any existing active subscriptions
        await self._cancel_existing_subscriptions(user_id)
        
        subscription = Subscription(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            plan=plan,
            provider=provider,
            provider_subscription_id=provider_subscription_id,
            provider_customer_id=provider_customer_id,
            status=SubscriptionStatus.active.value,
            current_period_start=datetime.utcnow(),
            current_period_end=current_period_end or datetime.utcnow() + timedelta(days=30),
            provider_metadata=provider_metadata,
        )
        
        self.db.add(subscription)
        
        # Upgrade user plan
        await self._upgrade_user_plan(user_id, plan)
        
        await self.db.commit()
        await self.db.refresh(subscription)
        
        return subscription
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        reason: Optional[str] = None,
        cancel_immediately: bool = False,
    ) -> Optional[Subscription]:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Subscription to cancel
            reason: Cancellation reason
            cancel_immediately: If True, cancel now. If False, cancel at period end.
        """
        result = await self.db.execute(
            select(Subscription).where(Subscription.id == uuid.UUID(subscription_id))
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return None
        
        subscription.cancelled_at = datetime.utcnow()
        subscription.cancellation_reason = reason
        
        if cancel_immediately:
            subscription.status = SubscriptionStatus.cancelled.value
            # Downgrade user to free plan
            await self._downgrade_user_plan(str(subscription.user_id))
        else:
            subscription.cancel_at_period_end = True
        
        await self.db.commit()
        await self.db.refresh(subscription)
        
        return subscription
    
    async def get_active_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get user's active subscription."""
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == uuid.UUID(user_id),
                    Subscription.status == SubscriptionStatus.active.value
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_subscription_by_provider_id(
        self,
        provider: str,
        provider_subscription_id: str,
    ) -> Optional[Subscription]:
        """Get subscription by provider's subscription ID."""
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.provider == provider,
                    Subscription.provider_subscription_id == provider_subscription_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def check_expired_subscriptions(self) -> int:
        """
        Check and expire subscriptions past their period end.
        
        Expires subscriptions that:
        1. Have passed current_period_end (regardless of cancel_at_period_end)
        2. Are marked for cancellation at period end
        
        Should be called periodically by a background job.
        Returns count of expired subscriptions.
        """
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        # Find all active/trialing/past_due subscriptions past their period end
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.status.in_([
                        SubscriptionStatus.active.value,
                        SubscriptionStatus.trialing.value,
                        SubscriptionStatus.past_due.value,
                    ]),
                    Subscription.current_period_end.isnot(None),
                    Subscription.current_period_end < now,
                    # Don't expire lifetime subscriptions
                    Subscription.is_lifetime == False,
                )
            )
        )
        
        expired_count = 0
        for subscription in result.scalars().all():
            subscription.status = SubscriptionStatus.expired.value
            await self._downgrade_user_plan(str(subscription.user_id))
            expired_count += 1
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Expired subscription {subscription.id} for user {subscription.user_id}")
        
        await self.db.commit()
        return expired_count
    
    # ==========================================
    # Helper Methods
    # ==========================================
    
    async def _upgrade_user_plan(self, user_id: str, plan: str) -> None:
        """Upgrade user's plan."""
        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.plan = plan
    
    async def _downgrade_user_plan(self, user_id: str) -> None:
        """Downgrade user to free plan."""
        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.plan = UserPlan.free.value
    
    async def _cancel_existing_subscriptions(self, user_id: str) -> None:
        """Cancel any existing active subscriptions for user."""
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == uuid.UUID(user_id),
                    Subscription.status == SubscriptionStatus.active.value
                )
            )
        )
        
        for subscription in result.scalars().all():
            subscription.status = SubscriptionStatus.cancelled.value
            subscription.cancelled_at = datetime.utcnow()
            subscription.cancellation_reason = "Replaced by new subscription"


# ==========================================
# Webhook Handler Stubs
# ==========================================

class LemonSqueezyWebhookHandler:
    """
    Stub for LemonSqueezy webhook handling.
    
    TODO: Implement actual webhook verification and processing.
    
    Webhooks to handle:
    - order_created: New order placed
    - subscription_created: New subscription started
    - subscription_updated: Subscription updated (renewal, upgrade/downgrade)
    - subscription_cancelled: Subscription cancelled
    - subscription_payment_success: Recurring payment successful
    - subscription_payment_failed: Recurring payment failed
    """
    
    def __init__(self, db: AsyncSession):
        self.payment_service = PaymentService(db)
    
    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        Handle LemonSqueezy webhook event.
        
        Returns True if handled successfully.
        """
        # TODO: Implement webhook signature verification
        # signature = request.headers.get("X-Signature")
        # if not verify_signature(payload, signature):
        #     return False
        
        handlers = {
            "order_created": self._handle_order_created,
            "subscription_created": self._handle_subscription_created,
            "subscription_cancelled": self._handle_subscription_cancelled,
            "subscription_payment_success": self._handle_payment_success,
            "subscription_payment_failed": self._handle_payment_failed,
        }
        
        handler = handlers.get(event_type)
        if handler:
            await handler(payload)
            return True
        
        return False
    
    async def _handle_order_created(self, payload: Dict[str, Any]) -> None:
        """Handle new order."""
        # TODO: Extract user_id, amount, plan from payload
        pass
    
    async def _handle_subscription_created(self, payload: Dict[str, Any]) -> None:
        """Handle new subscription."""
        # TODO: Create subscription record
        pass
    
    async def _handle_subscription_cancelled(self, payload: Dict[str, Any]) -> None:
        """Handle subscription cancellation."""
        # TODO: Cancel subscription
        pass
    
    async def _handle_payment_success(self, payload: Dict[str, Any]) -> None:
        """Handle successful payment."""
        # TODO: Mark payment as paid
        pass
    
    async def _handle_payment_failed(self, payload: Dict[str, Any]) -> None:
        """Handle failed payment."""
        # TODO: Mark payment as failed
        pass


class CoinbaseCommerceWebhookHandler:
    """
    Stub for Coinbase Commerce webhook handling.
    
    TODO: Implement actual webhook verification and processing.
    
    Webhooks to handle:
    - charge:created: New charge created
    - charge:confirmed: Payment confirmed
    - charge:failed: Payment failed
    - charge:pending: Payment pending
    """
    
    def __init__(self, db: AsyncSession):
        self.payment_service = PaymentService(db)
    
    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        Handle Coinbase Commerce webhook event.
        
        Returns True if handled successfully.
        """
        # TODO: Implement webhook signature verification
        # signature = request.headers.get("X-CC-Webhook-Signature")
        # if not verify_signature(payload, signature):
        #     return False
        
        handlers = {
            "charge:created": self._handle_charge_created,
            "charge:confirmed": self._handle_charge_confirmed,
            "charge:failed": self._handle_charge_failed,
            "charge:pending": self._handle_charge_pending,
        }
        
        handler = handlers.get(event_type)
        if handler:
            await handler(payload)
            return True
        
        return False
    
    async def _handle_charge_created(self, payload: Dict[str, Any]) -> None:
        """Handle new charge."""
        # TODO: Create pending payment record
        pass
    
    async def _handle_charge_confirmed(self, payload: Dict[str, Any]) -> None:
        """Handle confirmed charge."""
        # TODO: Mark payment as paid, create/extend subscription
        pass
    
    async def _handle_charge_failed(self, payload: Dict[str, Any]) -> None:
        """Handle failed charge."""
        # TODO: Mark payment as failed
        pass
    
    async def _handle_charge_pending(self, payload: Dict[str, Any]) -> None:
        """Handle pending charge."""
        # TODO: Update payment status
        pass

