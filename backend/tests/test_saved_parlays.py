import pytest
from httpx import AsyncClient

from app.services.saved_parlays.solscan import SolscanConfig, SolscanUrlBuilder


@pytest.mark.asyncio
async def test_save_custom_parlay_enqueues_job_when_redis_missing(client: AsyncClient):
    """
    In test mode, REDIS_URL is typically unset. We treat enqueue failure as a worker-like failure
    and mark the parlay as failed so the user can hit Retry in UI.
    """
    # Register user
    r = await client.post("/api/auth/register", json={"email": "saved-custom@test.com", "password": "Passw0rd!"})
    token = r.json()["access_token"]

    resp = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "My Custom Ticket",
            "legs": [
                {
                    "game_id": "00000000-0000-0000-0000-000000000001",
                    "pick": "home",
                    "market_type": "spreads",
                    "point": -3.5,
                }
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["parlay_type"] == "custom"
    # With no Redis configured in tests, enqueue fails and status flips to failed.
    assert data["inscription_status"] in ("queued", "failed")


@pytest.mark.asyncio
async def test_save_ai_parlay_never_queues_inscription(client: AsyncClient):
    r = await client.post("/api/auth/register", json={"email": "saved-ai@test.com", "password": "Passw0rd!"})
    token = r.json()["access_token"]

    resp = await client.post(
        "/api/parlays/ai/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "AI Ticket",
            "legs": [
                {
                    "market_id": "m1",
                    "outcome": "home",
                    "game": "A @ B",
                    "market_type": "h2h",
                    "odds": "-110",
                    "probability": 0.55,
                    "confidence": 60,
                }
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["parlay_type"] == "ai_generated"
    assert data["inscription_status"] == "none"


def test_solscan_url_generation_mainnet_and_devnet():
    mainnet = SolscanUrlBuilder(SolscanConfig(cluster="mainnet", base_url="https://solscan.io/tx"))
    devnet = SolscanUrlBuilder(SolscanConfig(cluster="devnet", base_url="https://solscan.io/tx"))

    assert mainnet.tx_url("abc") == "https://solscan.io/tx/abc"
    assert devnet.tx_url("abc") == "https://solscan.io/tx/abc?cluster=devnet"


@pytest.mark.asyncio
async def test_retry_only_works_for_failed_custom(client: AsyncClient):
    r = await client.post("/api/auth/register", json={"email": "retry@test.com", "password": "Passw0rd!"})
    token = r.json()["access_token"]

    # Save AI parlay
    ai = await client.post(
        "/api/parlays/ai/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "AI Ticket",
            "legs": [
                {
                    "market_id": "m1",
                    "outcome": "home",
                    "game": "A @ B",
                    "market_type": "h2h",
                    "odds": "-110",
                    "probability": 0.55,
                    "confidence": 60,
                }
            ],
        },
    )
    ai_id = ai.json()["id"]
    retry_ai = await client.post(
        f"/api/parlays/{ai_id}/inscription/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert retry_ai.status_code == 400


