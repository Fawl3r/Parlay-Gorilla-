from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.promo_code import PromoCode, PromoRewardType
from app.models.promo_redemption import PromoRedemption
from app.models.subscription import Subscription
from app.models.user import User, UserRole


async def _register_user(client: AsyncClient, *, email: str, password: str = "testpass123") -> str:
    res = await client.post("/api/auth/register", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


async def _make_admin(db: AsyncSession, *, email: str) -> None:
    row = (await db.execute(select(User).where(User.email == email))).scalar_one()
    row.role = UserRole.admin.value
    await db.commit()


@pytest.mark.asyncio
async def test_admin_create_and_user_redeem_credits_code(client: AsyncClient, db: AsyncSession):
    admin_email = f"admin-{uuid.uuid4()}@example.com"
    admin_token = await _register_user(client, email=admin_email)
    await _make_admin(db, email=admin_email)

    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    create_res = await client.post(
        "/api/admin/promo-codes",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "reward_type": "credits_3",
            "expires_at": expires_at,
            "max_uses_total": 2,
        },
    )
    assert create_res.status_code == 200
    promo_code = create_res.json()["code"]

    user_email = f"user-{uuid.uuid4()}@example.com"
    user_token = await _register_user(client, email=user_email)

    redeem_res = await client.post(
        "/api/promo-codes/redeem",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"code": promo_code},
    )
    assert redeem_res.status_code == 200
    payload = redeem_res.json()
    assert payload["success"] is True
    assert payload["reward_type"] == "credits_3"
    assert payload["credits_added"] == 3

    # One-time per account
    redeem_res2 = await client.post(
        "/api/promo-codes/redeem",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"code": promo_code},
    )
    assert redeem_res2.status_code == 409

    # Another account can redeem because max_uses_total=2
    user2_email = f"user2-{uuid.uuid4()}@example.com"
    user2_token = await _register_user(client, email=user2_email)
    redeem_res3 = await client.post(
        "/api/promo-codes/redeem",
        headers={"Authorization": f"Bearer {user2_token}"},
        json={"code": promo_code},
    )
    assert redeem_res3.status_code == 200

    # Total redemptions recorded
    count = await db.execute(select(func.count()).select_from(PromoRedemption))
    assert int(count.scalar_one() or 0) == 2


@pytest.mark.asyncio
async def test_redeem_expired_code_returns_410(client: AsyncClient, db: AsyncSession):
    # Create promo code directly in DB (expired)
    code = f"PG3C-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
    promo = PromoCode(
        code=code,
        reward_type=PromoRewardType.credits_3.value,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        max_uses_total=1,
        redeemed_count=0,
        is_active=True,
    )
    db.add(promo)
    await db.commit()

    user_email = f"user-{uuid.uuid4()}@example.com"
    user_token = await _register_user(client, email=user_email)

    redeem_res = await client.post(
        "/api/promo-codes/redeem",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"code": code},
    )
    assert redeem_res.status_code == 410


@pytest.mark.asyncio
async def test_premium_month_creates_subscription_and_stacks(client: AsyncClient, db: AsyncSession):
    admin_email = f"admin-{uuid.uuid4()}@example.com"
    admin_token = await _register_user(client, email=admin_email)
    await _make_admin(db, email=admin_email)

    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    codes: list[str] = []
    for _ in range(2):
        res = await client.post(
            "/api/admin/promo-codes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "reward_type": "premium_month",
                "expires_at": expires_at,
                "max_uses_total": 1,
            },
        )
        assert res.status_code == 200
        codes.append(res.json()["code"])

    user_email = f"user-{uuid.uuid4()}@example.com"
    user_token = await _register_user(client, email=user_email)

    # Redeem first
    res1 = await client.post(
        "/api/promo-codes/redeem",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"code": codes[0]},
    )
    assert res1.status_code == 200
    premium_until_1 = res1.json()["premium_until"]
    assert premium_until_1

    # Redeem second (should stack +30 days)
    res2 = await client.post(
        "/api/promo-codes/redeem",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"code": codes[1]},
    )
    assert res2.status_code == 200
    premium_until_2 = res2.json()["premium_until"]
    assert premium_until_2

    dt1 = datetime.fromisoformat(premium_until_1.replace("Z", "+00:00"))
    dt2 = datetime.fromisoformat(premium_until_2.replace("Z", "+00:00"))
    assert dt2 > dt1
    assert dt2 - dt1 >= timedelta(days=29)  # allow minor clock skew

    # Subscription rows exist
    subs = (
        await db.execute(select(Subscription).order_by(Subscription.created_at.asc()))
    ).scalars().all()
    assert len(subs) >= 2


