"""
Admin API smoke tests.

Ensures all critical admin endpoints return 200 with valid JSON even with:
- empty database
- no seed data
- missing analytics/telemetry tables

No admin endpoint may return HTTP 500 from unhandled exceptions.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.dependencies import get_current_user
from app.models.user import UserRole


class _FakeAdminUser:
    """Minimal object that passes require_admin and attribute access in admin routes."""
    id = uuid.uuid4()
    email = "admin@test.local"
    role = UserRole.admin.value
    plan = "free"
    is_active = True
    username = None
    subscription_plan = None
    subscription_status = None
    created_at = None
    last_login = None


@pytest.fixture
def admin_client():
    """Override get_current_user so admin routes see an admin user (no token needed)."""
    async def _get_current_user_admin():
        return _FakeAdminUser()

    app.dependency_overrides[get_current_user] = _get_current_user_admin
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# Endpoints that must return 200 with valid JSON (safe fallbacks when DB empty/missing tables)
ADMIN_GET_ENDPOINTS = [
    "/api/admin/safety",
    "/api/admin/metrics/overview",
    "/api/admin/metrics/users",
    "/api/admin/metrics/usage",
    "/api/admin/metrics/revenue",
    "/api/admin/logs",
    "/api/admin/logs/stats",
    "/api/admin/logs/sources",
]


@pytest.mark.asyncio
async def test_admin_safety_returns_200(client: AsyncClient, admin_client):
    """GET /api/admin/safety returns 200 and valid JSON."""
    resp = await client.get("/api/admin/safety")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "health_score" in data
    assert "state" in data
    assert "recommended_action" in data


@pytest.mark.asyncio
async def test_admin_metrics_overview_returns_200(client: AsyncClient, admin_client):
    """GET /api/admin/metrics/overview returns 200 and valid JSON."""
    resp = await client.get("/api/admin/metrics/overview")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "total_users" in data or "time_range" in data


@pytest.mark.asyncio
async def test_admin_metrics_users_returns_200(client: AsyncClient, admin_client):
    """GET /api/admin/metrics/users returns 200 and valid JSON."""
    resp = await client.get("/api/admin/metrics/users")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "total_users" in data or "time_range" in data


@pytest.mark.asyncio
async def test_admin_metrics_usage_returns_200(client: AsyncClient, admin_client):
    """GET /api/admin/metrics/usage returns 200 and valid JSON."""
    resp = await client.get("/api/admin/metrics/usage")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_admin_metrics_revenue_returns_200(client: AsyncClient, admin_client):
    """GET /api/admin/metrics/revenue returns 200 and valid JSON."""
    resp = await client.get("/api/admin/metrics/revenue")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_admin_logs_list_returns_200(client: AsyncClient, admin_client):
    """GET /api/admin/logs returns 200 and valid JSON (list)."""
    resp = await client.get("/api/admin/logs")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_admin_logs_stats_returns_200(client: AsyncClient, admin_client):
    """GET /api/admin/logs/stats returns 200 and valid JSON."""
    resp = await client.get("/api/admin/logs/stats")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "total" in data
    assert "error_rate" in data


@pytest.mark.asyncio
async def test_admin_logs_sources_returns_200(client: AsyncClient, admin_client):
    """GET /api/admin/logs/sources returns 200 and valid JSON (list)."""
    resp = await client.get("/api/admin/logs/sources")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_all_admin_smoke_endpoints_return_200(client: AsyncClient, admin_client):
    """All critical admin GET endpoints return 200 with valid JSON (no 500)."""
    for path in ADMIN_GET_ENDPOINTS:
        resp = await client.get(path)
        assert resp.status_code == 200, f"{path} returned {resp.status_code}: {resp.text}"
        # Ensure response is JSON (no stack trace or HTML)
        data = resp.json()
        assert data is not None
