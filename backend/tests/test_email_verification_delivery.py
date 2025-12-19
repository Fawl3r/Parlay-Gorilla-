import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_resend_verification_returns_503_when_email_not_configured(client: AsyncClient):
    """
    In tests, RESEND_API_KEY is intentionally unset.
    The API should surface that email sending is unavailable (instead of pretending success).
    """
    email = f"resend-{uuid.uuid4()}@example.com"
    r = await client.post("/api/auth/register", json={"email": email, "password": "testpass123"})
    assert r.status_code == 200

    token = r.json()["access_token"]

    resend = await client.post(
        "/api/auth/resend-verification",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resend.status_code == 503
    assert "Unable to send verification email" in resend.json()["detail"]


@pytest.mark.asyncio
async def test_profile_completed_auto_marked_when_display_name_present(client: AsyncClient, db: AsyncSession):
    """
    Regression guard for redirect loops:
    if a user has display_name filled in but profile_completed is False (older rows),
    `GET /api/auth/me` should auto-correct it.
    """
    user_id = uuid.uuid4()
    email = f"autoprofile-{uuid.uuid4()}@example.com"

    user = User(
        id=user_id,
        email=email,
        password_hash=get_password_hash("testpass123"),
        display_name="Already Set",
        profile_completed=False,
        email_verified=True,
    )
    db.add(user)
    await db.commit()

    token = create_access_token({"sub": str(user_id), "email": email})

    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["profile_completed"] is True

    # Verify persisted to DB
    await db.refresh(user)
    assert user.profile_completed is True


