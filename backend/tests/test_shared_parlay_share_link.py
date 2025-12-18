"""Regression tests for shared parlay link viewing.

The share-link endpoint previously triggered async SQLAlchemy lazy-loading of
`SharedParlay.user`, which can raise:
  greenlet_spawn has not been called; can't call await_only() here
"""

from __future__ import annotations

from decimal import Decimal
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.models.parlay import Parlay
from app.models.shared_parlay import SharedParlay
from app.models.user import User


@pytest.mark.asyncio
async def test_get_shared_parlay_returns_user_display_name_and_increments_views(
    client: AsyncClient,
    db: AsyncSession,
):
    user_id = uuid.uuid4()
    parlay_id = uuid.uuid4()
    share_token = f"test-share-{uuid.uuid4().hex}"

    user = User(
        id=user_id,
        email=f"share-link-{uuid.uuid4()}@example.com",
        username="sharetester",
        display_name="Share Tester",
    )
    parlay = Parlay(
        id=parlay_id,
        user_id=user_id,
        legs=[{"market_id": "m1", "outcome": "home"}],
        num_legs=1,
        parlay_hit_prob=Decimal("0.2500"),
        risk_profile="balanced",
        ai_summary="test summary",
        ai_risk_notes="test notes",
    )
    shared = SharedParlay(
        parlay_id=parlay_id,
        user_id=user_id,
        share_token=share_token,
        is_public="public",
        views_count=0,
        likes_count=0,
        comment="check this out",
    )

    db.add_all([user, parlay, shared])
    await db.commit()

    response = await client.get(f"/api/social/share/{share_token}")
    assert response.status_code == 200

    payload = response.json()
    assert payload["user"]["display_name"] == "Share Tester"
    assert payload["shared"]["views_count"] == 1

    # Cleanup: keep test suite order-independent (other tests assume empty social feed).
    await db.execute(delete(SharedParlay).where(SharedParlay.share_token == share_token))
    await db.execute(delete(Parlay).where(Parlay.id == parlay_id))
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()


