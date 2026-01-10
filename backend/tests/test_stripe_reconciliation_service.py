import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.models.subscription import Subscription
from app.models.user import User
from app.services.stripe_reconciliation_service import StripeReconciliationService


@pytest.mark.asyncio
async def test_reconcile_latest_credit_pack_applies_credits(db, monkeypatch):
    # Ensure Stripe is "configured" for the service under test.
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_dummy", raising=False)

    user = User(
        id=uuid.uuid4(),
        email="credits@example.com",
        stripe_customer_id="cus_test_123",
        credit_balance=0,
    )
    db.add(user)
    await db.commit()

    # Stripe checkout session list returns newest first.
    session = {
        "id": "cs_test_credits_1",
        "mode": "payment",
        "status": "complete",
        "payment_status": "paid",
        "customer": "cus_test_123",
        "metadata": {
            "user_id": str(user.id),
            "purchase_type": "credit_pack",
            "credit_pack_id": "credits_10",
        },
    }

    import stripe

    monkeypatch.setattr(stripe.checkout.Session, "list", lambda **_: {"data": [session]})

    service = StripeReconciliationService(db)
    result = await service.reconcile_latest_for_user(user=user)

    assert result.status == "applied"

    refreshed = await db.get(User, user.id)
    assert refreshed is not None
    assert int(refreshed.credit_balance or 0) > 0


@pytest.mark.asyncio
async def test_reconcile_session_subscription_active_creates_subscription(db, monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_dummy", raising=False)

    user = User(
        id=uuid.uuid4(),
        email="sub@example.com",
        stripe_customer_id="cus_test_456",
    )
    db.add(user)
    await db.commit()

    session_id = "cs_test_sub_1"
    subscription_id = "sub_test_1"

    session = {
        "id": session_id,
        "mode": "subscription",
        "customer": "cus_test_456",
        "metadata": {
            "user_id": str(user.id),
            "plan_code": "PG_PRO_MONTHLY",
        },
        "subscription": subscription_id,
    }

    now = datetime.now(timezone.utc)
    subscription = {
        "id": subscription_id,
        "customer": "cus_test_456",
        "status": "active",
        "metadata": {
            "user_id": str(user.id),
            "plan_code": "PG_PRO_MONTHLY",
        },
        "current_period_start": int(now.timestamp()),
        "current_period_end": int((now + timedelta(days=30)).timestamp()),
    }

    import stripe

    monkeypatch.setattr(stripe.checkout.Session, "retrieve", lambda _id: session)
    monkeypatch.setattr(stripe.Subscription, "retrieve", lambda _id: subscription)

    service = StripeReconciliationService(db)
    result = await service.reconcile_session_for_user(user=user, session_id=session_id)

    assert result.status == "applied"
    assert result.subscription_id == subscription_id

    # Subscription record created
    sub_row = (await db.execute(
        Subscription.__table__.select().where(Subscription.provider_subscription_id == subscription_id)
    )).first()
    assert sub_row is not None

    refreshed = await db.get(User, user.id)
    assert refreshed is not None
    assert refreshed.stripe_subscription_id == subscription_id
    assert refreshed.subscription_status == "active"


