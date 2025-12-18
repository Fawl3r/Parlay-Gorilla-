import pytest
import httpx
from fastapi import HTTPException
from httpx import ASGITransport

from app.main import app
from app.api.routes.admin.auth import require_admin
from app.services import admin_affiliate_service


@pytest.fixture(autouse=True)
def clear_overrides():
    original = dict(app.dependency_overrides)
    yield
    app.dependency_overrides = original


@pytest.mark.asyncio
async def test_admin_affiliates_requires_admin():
    """Endpoint should return 403 when admin check fails."""

    async def fake_require_admin():
        raise HTTPException(status_code=403, detail="forbidden")

    app.dependency_overrides[require_admin] = fake_require_admin

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/admin/affiliates")
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_affiliates_returns_data(monkeypatch):
    """Endpoint should forward params and return list payload."""
    captured = {}

    async def fake_require_admin():
        return {"id": "admin"}

    async def fake_list_affiliates(self, **kwargs):
        captured.update(kwargs)
        return {
            "total": 1,
            "page": kwargs.get("page", 1),
            "page_size": kwargs.get("page_size", 25),
            "items": [
                {
                    "id": "aff-1",
                    "user_id": "user-1",
                    "email": "a@test.com",
                    "username": "tester",
                    "referral_code": "CODE123",
                    "tier": "rookie",
                    "created_at": None,
                    "is_active": True,
                    "stats": {
                        "clicks": 10,
                        "referrals": 3,
                        "conversion_rate": 30.0,
                        "revenue": 120.0,
                        "commission_earned": 24.0,
                        "commission_paid": 10.0,
                        "pending_commission": 14.0,
                    },
                }
            ],
            "time_range": kwargs.get("time_range", "30d"),
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-01-02T00:00:00Z",
        }

    app.dependency_overrides[require_admin] = fake_require_admin
    monkeypatch.setattr(
        admin_affiliate_service.AdminAffiliateService, "list_affiliates", fake_list_affiliates
    )

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/admin/affiliates?time_range=7d&page=2&page_size=10&search=code&sort=revenue_asc"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["referral_code"] == "CODE123"

    # Ensure params were forwarded
    assert captured["time_range"] == "7d"
    assert captured["page"] == 2
    assert captured["page_size"] == 10
    assert captured["search"] == "code"
    assert captured["sort"] == "revenue_asc"


