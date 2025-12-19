"""
Hybrid affiliate system integration tests.

Ensures:
- Cookie attribution works on /api/auth/register
- Settlement routing marks LemonSqueezy webhooks as `settlement_provider=lemonsqueezy`
- Coinbase webhooks default to `settlement_provider=internal`
- Internal payout selection ignores LemonSqueezy-settled commissions
"""

from __future__ import annotations

from decimal import Decimal
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate import Affiliate
from app.models.affiliate_commission import AffiliateCommission, CommissionSettlementProvider, CommissionStatus
from app.models.subscription_plan import BillingCycle, PaymentProvider, SubscriptionPlan
from app.models.user import User
from app.services.payout_service import PayoutService


async def _register_user(client: AsyncClient, prefix: str) -> tuple[str, str]:
    email = f"{prefix}-{uuid.uuid4()}@example.com"
    r = await client.post("/api/auth/register", json={"email": email, "password": "testpass123"})
    assert r.status_code == 200
    data = r.json()
    return data["user"]["id"], data["access_token"]


async def _register_affiliate(client: AsyncClient) -> dict:
    _user_id, token = await _register_user(client, "aff")
    r = await client.post(
        "/api/affiliates/register",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    return r.json()


async def _ensure_plan(db: AsyncSession, code: str, billing_cycle: str, provider: str, price_cents: int):
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == code))
    existing = result.scalar_one_or_none()
    if existing:
        return

    db.add(
        SubscriptionPlan(
            code=code,
            name=code,
            description=code,
            price_cents=price_cents,
            currency="USD",
            billing_cycle=billing_cycle,
            provider=provider,
            is_active=True,
            is_featured=False,
            max_ai_parlays_per_day=-1,
            can_use_custom_builder=True,
            can_use_upset_finder=True,
            can_use_multi_sport=True,
            can_save_parlays=True,
            ad_free=True,
        )
    )
    await db.commit()


@pytest.mark.asyncio
async def test_affiliate_cookie_attribution_happens_on_register(client: AsyncClient, db: AsyncSession):
    affiliate = await _register_affiliate(client)
    referral_code = affiliate["referral_code"]

    # Landing click should set cookies on the client.
    click = await client.post("/api/affiliates/click", json={"referral_code": referral_code, "landing_page": "/"})
    assert click.status_code == 200
    assert click.json()["success"] is True
    assert client.cookies.get("pg_affiliate_ref") == referral_code
    assert client.cookies.get("pg_affiliate_click") is not None

    referred_user_id, _token = await _register_user(client, "referred")

    # User should be attributed in DB.
    user = (await db.execute(select(User).where(User.id == uuid.UUID(referred_user_id)))).scalar_one()
    assert user.referred_by_affiliate_id is not None
    assert str(user.referred_by_affiliate_id) == affiliate["id"]

    # Cookies should be consumed/cleared by the auth flow.
    assert client.cookies.get("pg_affiliate_ref") is None
    assert client.cookies.get("pg_affiliate_click") is None


@pytest.mark.asyncio
async def test_lemonsqueezy_subscription_webhook_creates_ls_settled_commission(client: AsyncClient, db: AsyncSession):
    affiliate = await _register_affiliate(client)
    referral_code = affiliate["referral_code"]

    # Attribute a new user to this affiliate via cookies.
    await client.post("/api/affiliates/click", json={"referral_code": referral_code, "landing_page": "/"})
    user_id, _token = await _register_user(client, "lsbuyer")

    subscription_id = f"ls_sub_{uuid.uuid4()}"
    webhook_id = f"ls_evt_{uuid.uuid4()}"

    payload = {
        "meta": {"event_name": "subscription_created", "webhook_id": webhook_id},
        "data": {
            "id": subscription_id,
            "attributes": {
                "customer_id": "test_customer",
                "total": 1999,
                "renews_at": "2030-01-01T00:00:00Z",
                "created_at": "2030-01-01T00:00:00Z",
                "variant_name": "PG Premium Monthly",
                "first_subscription_item": {"custom_data": {"user_id": user_id, "plan_code": "PG_PREMIUM_MONTHLY"}},
            },
        },
    }

    r = await client.post("/api/webhooks/lemonsqueezy", json=payload)
    assert r.status_code == 200

    commission = (
        await db.execute(select(AffiliateCommission).where(AffiliateCommission.sale_id == subscription_id))
    ).scalar_one()
    assert commission.settlement_provider == CommissionSettlementProvider.LEMONSQUEEZY.value


@pytest.mark.asyncio
async def test_coinbase_subscription_webhook_creates_internal_settled_commission(client: AsyncClient, db: AsyncSession):
    affiliate = await _register_affiliate(client)
    referral_code = affiliate["referral_code"]

    # Attribute a new user to this affiliate via cookies.
    await client.post("/api/affiliates/click", json={"referral_code": referral_code, "landing_page": "/"})
    user_id, _token = await _register_user(client, "cbbuyer")

    await _ensure_plan(
        db,
        "PG_PREMIUM_MONTHLY_CRYPTO",
        BillingCycle.monthly.value,
        PaymentProvider.coinbase.value,
        1999,
    )

    charge_id = f"cb_charge_{uuid.uuid4()}"
    event_id = f"cb_evt_{uuid.uuid4()}"

    payload = {
        "id": event_id,
        "event": {
            "type": "charge:confirmed",
            "data": {
                "id": charge_id,
                "pricing": {"local": {"amount": "19.99", "currency": "USD"}},
                "metadata": {"user_id": user_id, "plan_code": "PG_PREMIUM_MONTHLY_CRYPTO"},
            },
        },
    }

    r = await client.post("/api/webhooks/coinbase", json=payload)
    assert r.status_code == 200

    commission = (await db.execute(select(AffiliateCommission).where(AffiliateCommission.sale_id == charge_id))).scalar_one()
    assert commission.settlement_provider == CommissionSettlementProvider.INTERNAL.value


@pytest.mark.asyncio
async def test_payout_service_excludes_lemonsqueezy_settled_commissions(db: AsyncSession):
    # Create a user + affiliate directly (we only need IDs for the payout query).
    affiliate_user = User(id=uuid.uuid4(), email=f"payout-aff-{uuid.uuid4()}@example.com")
    db.add(affiliate_user)
    await db.commit()

    affiliate = Affiliate.create_with_referral_code(affiliate_user.id)
    db.add(affiliate)

    # Create two READY commissions: one internal, one lemonsqueezy.
    internal_commission = AffiliateCommission.create_commission(
        affiliate_id=affiliate.id,
        referred_user_id=uuid.uuid4(),
        sale_id=f"sale_internal_{uuid.uuid4()}",
        sale_type="subscription",
        base_amount=Decimal("500.00"),
        commission_rate=Decimal("0.20"),
        settlement_provider=CommissionSettlementProvider.INTERNAL.value,
    )
    internal_commission.mark_ready()

    ls_commission = AffiliateCommission.create_commission(
        affiliate_id=affiliate.id,
        referred_user_id=uuid.uuid4(),
        sale_id=f"sale_ls_{uuid.uuid4()}",
        sale_type="subscription",
        base_amount=Decimal("500.00"),
        commission_rate=Decimal("0.20"),
        settlement_provider=CommissionSettlementProvider.LEMONSQUEEZY.value,
    )
    ls_commission.mark_ready()

    db.add_all([internal_commission, ls_commission])
    await db.commit()

    payout_service = PayoutService(db)
    ready = await payout_service.get_ready_commissions_for_affiliate(str(affiliate.id))

    assert len(ready) == 1
    assert ready[0].id == internal_commission.id
    assert ready[0].settlement_provider == CommissionSettlementProvider.INTERNAL.value
    assert ready[0].status == CommissionStatus.READY.value


