"""Tests for /api/billing/status balances payload."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_billing_status_includes_balances(client: AsyncClient):
    # Register
    email = "balances-test@example.com"
    password = "testpass123"
    reg = await client.post("/api/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]

    # Fetch billing status
    res = await client.get("/api/billing/status", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200, res.text
    data = res.json()

    assert "balances" in data
    balances = data["balances"]

    # Required keys (contract)
    for key in [
        "credit_balance",
        "free_parlays_total",
        "free_parlays_used",
        "free_parlays_remaining",
        "daily_ai_limit",
        "daily_ai_used",
        "daily_ai_remaining",
        "premium_ai_parlays_used",
        "premium_ai_period_start",
    ]:
        assert key in balances


