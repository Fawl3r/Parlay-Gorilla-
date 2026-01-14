import pytest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_check_parlay_access_uses_credits_when_free_exhausted(monkeypatch):
    """
    When a non-premium user has no free parlays remaining but has enough credits,
    access_control.check_parlay_access_with_purchase() should allow generation via credits.
    """
    from app.core import access_control

    class FakeSubscriptionService:
        def __init__(self, db):
            self.db = db

        async def is_user_premium(self, user_id: str) -> bool:
            return False

        async def get_remaining_free_parlays(self, user_id: str) -> int:
            return 0

    class FakeParlayPurchaseService:
        def __init__(self, db):
            self.db = db

        async def has_unused_purchase(self, user_id: str, is_multi_sport: bool = False) -> bool:
            return False

    # Patch services used inside access_control.
    monkeypatch.setattr(access_control, "SubscriptionService", FakeSubscriptionService)
    monkeypatch.setattr(
        access_control,
        "ParlayPurchaseService",
        FakeParlayPurchaseService,
        raising=False,
    )
    import app.services.parlay_purchase_service as purchase_module

    monkeypatch.setattr(purchase_module, "ParlayPurchaseService", FakeParlayPurchaseService)

    user = SimpleNamespace(id=uuid.uuid4(), credit_balance=10)
    db = AsyncMock()

    info = await access_control.check_parlay_access_with_purchase(user=user, db=db, is_multi_sport=False)

    assert info["can_generate"] is True
    assert info["use_credits"] is True
    assert info["credits_required"] == 3


@pytest.mark.asyncio
async def test_check_parlay_access_triple_requires_credits(monkeypatch):
    """
    Triple parlays count as 3 usages, so credit users must have enough credits for 3 units.
    """
    from app.core import access_control

    class FakeSubscriptionService:
        def __init__(self, db):
            self.db = db

        async def is_user_premium(self, user_id: str) -> bool:
            return False

        async def get_remaining_free_parlays(self, user_id: str) -> int:
            return 0

    class FakeParlayPurchaseService:
        def __init__(self, db):
            self.db = db

        async def has_unused_purchase(self, user_id: str, is_multi_sport: bool = False) -> bool:
            return False

    monkeypatch.setattr(access_control, "SubscriptionService", FakeSubscriptionService)
    import app.services.parlay_purchase_service as purchase_module

    monkeypatch.setattr(purchase_module, "ParlayPurchaseService", FakeParlayPurchaseService)

    # With default credit cost of 3 per usage, 3 units require 9 credits.
    user = SimpleNamespace(id=uuid.uuid4(), credit_balance=8)
    db = AsyncMock()

    info = await access_control.check_parlay_access_with_purchase(
        user=user,
        db=db,
        is_multi_sport=False,
        usage_units=3,
        allow_purchases=False,
    )

    assert info["can_generate"] is False
    assert info["credits_required"] == 9


@pytest.mark.asyncio
async def test_custom_builder_access_allows_credit_users(monkeypatch):
    from app.core import access_control

    class FakeSubscriptionService:
        def __init__(self, db):
            self.db = db

        async def is_user_premium(self, user_id: str) -> bool:
            return False

        async def can_use_free_custom_builder(self, user_id: str) -> bool:
            # Force credit path for this test (no free custom builder usage available).
            return False

    monkeypatch.setattr(access_control, "SubscriptionService", FakeSubscriptionService)

    user = SimpleNamespace(id=uuid.uuid4(), credit_balance=10)
    db = AsyncMock()

    out = await access_control.require_custom_builder_access(user=user, db=db)
    assert out.user is user
    assert out.use_credits is True
    assert out.credits_required > 0


