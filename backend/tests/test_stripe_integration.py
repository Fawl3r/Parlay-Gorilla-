"""
Tests for Stripe integration.

Tests checkout session creation, portal session creation, webhook handling,
and subscription state synchronization.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import uuid

from app.services.stripe_service import StripeService
from app.models.user import SubscriptionStatusEnum, User
from app.models.subscription_plan import SubscriptionPlan
from app.models.subscription import Subscription, SubscriptionStatus


@pytest.fixture
def mock_stripe():
    """Mock Stripe SDK."""
    # Stripe SDK is referenced from the checkout manager module after refactor.
    with patch("app.services.stripe.stripe_checkout_manager.stripe") as mock:
        yield mock


@pytest.fixture
def stripe_service(db):
    """Create StripeService instance."""
    return StripeService(db)


@pytest.fixture
def sample_user(db):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        account_number="test1234567890123456",
        password_hash="hashed",
    )
    db.add(user)
    return user


@pytest.fixture
def sample_plan():
    """Create a test subscription plan."""
    return SubscriptionPlan(
        id=uuid.uuid4(),
        code="PG_PRO_MONTHLY",
        name="Pro Monthly",
        provider="stripe",
        provider_product_id="price_test123",
        is_active=True,
    )


@pytest.mark.asyncio
async def test_create_checkout_session(stripe_service, mock_stripe, sample_user, sample_plan, db):
    """Test creating a Stripe checkout session."""
    # Mock Stripe customer creation
    mock_customer = MagicMock()
    mock_customer.id = "cus_test123"
    mock_stripe.Customer.create.return_value = mock_customer
    
    # Mock checkout session creation
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/test"
    mock_stripe.checkout.Session.create.return_value = mock_session
    
    # Mock settings
    with patch("app.services.stripe.stripe_checkout_manager.settings") as mock_settings:
        mock_settings.stripe_secret_key = "sk_test_123"
        mock_settings.stripe_success_url = "{app_url}/billing/success?provider=stripe"
        mock_settings.stripe_cancel_url = "{app_url}/billing?canceled=true"
        mock_settings.app_url = "http://localhost:3000"
        
        await db.commit()
        await db.refresh(sample_user)
        
        checkout_url = await stripe_service.create_checkout_session(
            user=sample_user,
            plan=sample_plan,
        )
        
        assert checkout_url == "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_portal_session(stripe_service, mock_stripe, sample_user, db):
    """Test creating a Stripe portal session."""
    sample_user.stripe_customer_id = "cus_test123"
    await db.commit()
    await db.refresh(sample_user)
    
    # Mock portal session creation
    mock_session = MagicMock()
    mock_session.url = "https://billing.stripe.com/test"
    mock_stripe.billing_portal.Session.create.return_value = mock_session
    
    # Mock settings
    with patch("app.services.stripe.stripe_checkout_manager.settings") as mock_settings:
        mock_settings.stripe_secret_key = "sk_test_123"
        mock_settings.app_url = "http://localhost:3000"
        
        portal_url = await stripe_service.create_portal_session(user=sample_user)
        
        assert portal_url == "https://billing.stripe.com/test"
        mock_stripe.billing_portal.Session.create.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_subscription_created(stripe_service, db, sample_user):
    """Test handling subscription.created webhook event."""
    event = {
        "type": "customer.subscription.created",
        "id": "evt_test123",
        "data": {
            "object": {
                "id": "sub_test123",
                "customer": "cus_test123",
                "status": "active",
                "current_period_start": 1609459200,  # 2021-01-01
                "current_period_end": 1612137600,  # 2021-02-01
                "metadata": {
                    "user_id": str(sample_user.id),
                    "plan_code": "PG_PRO_MONTHLY",
                },
            }
        },
    }
    
    sample_user.stripe_customer_id = "cus_test123"
    await db.commit()
    await db.refresh(sample_user)
    
    await stripe_service.sync_subscription_from_webhook(event)
    
    # Verify subscription was created
    from sqlalchemy import select
    result = await db.execute(
        select(Subscription).where(Subscription.provider_subscription_id == "sub_test123")
    )
    subscription = result.scalar_one_or_none()
    
    assert subscription is not None
    assert subscription.status == SubscriptionStatus.active.value
    assert subscription.provider == "stripe"
    assert subscription.plan == "PG_PRO_MONTHLY"

    # Verify user fields are updated consistently for access control
    await db.refresh(sample_user)
    assert sample_user.subscription_plan == "PG_PRO_MONTHLY"
    assert sample_user.subscription_status == SubscriptionStatusEnum.active.value
    assert sample_user.stripe_subscription_id == "sub_test123"


@pytest.mark.asyncio
async def test_webhook_invoice_paid_resets_usage(stripe_service, db, sample_user):
    """Test that invoice.paid event resets usage counters."""
    # Create existing subscription
    subscription = Subscription(
        user_id=sample_user.id,
        plan="PG_PRO_MONTHLY",
        provider="stripe",
        provider_subscription_id="sub_test123",
        status=SubscriptionStatus.active.value,
        current_period_start=datetime.now(timezone.utc),
        current_period_end=datetime.now(timezone.utc),
    )
    db.add(subscription)
    
    # Set usage counters
    sample_user.premium_ai_parlays_used = 50
    sample_user.premium_custom_builder_used = 10
    await db.commit()
    await db.refresh(sample_user)
    
    event = {
        "type": "invoice.paid",
        "data": {
            "object": {
                "subscription": "sub_test123",
            }
        },
    }
    
    await stripe_service.sync_subscription_from_webhook(event)
    await db.refresh(sample_user)
    
    # Verify usage was reset
    assert sample_user.premium_ai_parlays_used == 0
    assert sample_user.premium_custom_builder_used == 0


@pytest.mark.asyncio
async def test_webhook_subscription_deleted(stripe_service, db, sample_user):
    """Test handling subscription.deleted webhook event."""
    # Create active subscription
    subscription = Subscription(
        user_id=sample_user.id,
        plan="PG_PRO_MONTHLY",
        provider="stripe",
        provider_subscription_id="sub_test123",
        status=SubscriptionStatus.active.value,
        current_period_start=datetime.now(timezone.utc),
        current_period_end=datetime.now(timezone.utc),
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    
    event = {
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_test123",
            }
        },
    }
    
    await stripe_service.sync_subscription_from_webhook(event)
    await db.refresh(subscription)
    
    assert subscription.status == SubscriptionStatus.cancelled.value
    assert subscription.cancelled_at is not None


@pytest.mark.asyncio
async def test_webhook_subscription_updated_plan_change_maps_price_to_plan_code(stripe_service, db, sample_user):
    """
    Plan changes performed in Stripe Customer Portal do NOT update subscription metadata.
    We must derive the plan code from the subscription item price id.
    """
    # Seed plan rows so price id -> plan code lookup works
    plan_monthly = SubscriptionPlan(
        id=uuid.uuid4(),
        code="PG_PRO_MONTHLY",
        name="Pro Monthly",
        provider="stripe",
        provider_price_id="price_monthly_test",
        is_active=True,
    )
    plan_annual = SubscriptionPlan(
        id=uuid.uuid4(),
        code="PG_PRO_ANNUAL",
        name="Pro Annual",
        provider="stripe",
        provider_price_id="price_annual_test",
        is_active=True,
    )
    db.add(plan_monthly)
    db.add(plan_annual)

    # Existing subscription row
    sub = Subscription(
        user_id=sample_user.id,
        plan="PG_PRO_MONTHLY",
        provider="stripe",
        provider_subscription_id="sub_test123",
        provider_customer_id="cus_test123",
        status=SubscriptionStatus.active.value,
        current_period_start=datetime.now(timezone.utc),
        current_period_end=datetime.now(timezone.utc),
    )
    db.add(sub)
    sample_user.stripe_customer_id = "cus_test123"
    sample_user.stripe_subscription_id = "sub_test123"
    sample_user.subscription_plan = "PG_PRO_MONTHLY"
    sample_user.subscription_status = SubscriptionStatusEnum.active.value

    await db.commit()

    # Stripe portal plan change: metadata stays monthly, items.price.id changes to annual
    event = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test123",
                "customer": "cus_test123",
                "status": "active",
                "metadata": {
                    "user_id": str(sample_user.id),
                    "plan_code": "PG_PRO_MONTHLY",
                },
                "items": {
                    "data": [
                        {
                            "price": {"id": "price_annual_test"},
                        }
                    ]
                },
            }
        },
    }

    await stripe_service.sync_subscription_from_webhook(event)

    from sqlalchemy import select

    updated = (
        await db.execute(select(Subscription).where(Subscription.provider_subscription_id == "sub_test123"))
    ).scalar_one()

    assert updated.plan == "PG_PRO_ANNUAL"

    await db.refresh(sample_user)
    assert sample_user.subscription_plan == "PG_PRO_ANNUAL"
    assert sample_user.subscription_status == SubscriptionStatusEnum.active.value


@pytest.mark.asyncio
async def test_webhook_subscription_updated_incomplete_does_not_flip_user_to_free(stripe_service, db, sample_user):
    """
    Some upgrade flows can briefly report `incomplete`. We treat this as a past_due-style grace state
    so the app doesn't show the user as "Free" while payment is processing.
    """
    # Existing subscription row
    sub = Subscription(
        user_id=sample_user.id,
        plan="PG_PRO_MONTHLY",
        provider="stripe",
        provider_subscription_id="sub_test123",
        provider_customer_id="cus_test123",
        status=SubscriptionStatus.active.value,
        current_period_start=datetime.now(timezone.utc),
        current_period_end=datetime.now(timezone.utc),
    )
    db.add(sub)
    sample_user.subscription_plan = "PG_PRO_MONTHLY"
    sample_user.subscription_status = SubscriptionStatusEnum.active.value
    await db.commit()

    event = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test123",
                "customer": "cus_test123",
                "status": "incomplete",
                "metadata": {"user_id": str(sample_user.id), "plan_code": "PG_PRO_MONTHLY"},
            }
        },
    }

    await stripe_service.sync_subscription_from_webhook(event)

    from sqlalchemy import select

    updated = (
        await db.execute(select(Subscription).where(Subscription.provider_subscription_id == "sub_test123"))
    ).scalar_one()

    assert updated.status == SubscriptionStatus.past_due.value

    await db.refresh(sample_user)
    assert sample_user.subscription_status == SubscriptionStatusEnum.active.value

