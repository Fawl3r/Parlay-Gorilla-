"""Regression tests for GET /api/public/todays-top-picks."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


def _fake_candidate_legs():
    """Minimal candidate leg dicts matching what candidate_leg_service builds."""
    return [
        {
            "game_id": "09fd4dd8-61bc-4e98-9c25-1efb523f6aea",
            "game": "Seattle Kraken @ Dallas Stars",
            "home_team": "Dallas Stars",
            "away_team": "Seattle Kraken",
            "market_type": "h2h",
            "outcome": "home",
            "odds": "-150",
            "confidence_score": 84.5,
            "start_time": (datetime.now(timezone.utc).isoformat()),
        },
        {
            "game_id": "2a743722-b549-45e3-b564-2b10e43a3b06",
            "game": "Flyers @ Capitals",
            "home_team": "Washington Capitals",
            "away_team": "Philadelphia Flyers",
            "market_type": "h2h",
            "outcome": "away",
            "odds": "+120",
            "confidence_score": 82.0,
            "start_time": (datetime.now(timezone.utc).isoformat()),
        },
    ]


@pytest.mark.asyncio
async def test_todays_top_picks_returns_picks_when_pipeline_has_candidates(client: AsyncClient):
    """When the pipeline returns candidate legs, the endpoint returns them as picks (no extra filter)."""
    fake_legs = _fake_candidate_legs()

    class FakeEngine:
        def get_candidate_legs(self, **kwargs):
            return AsyncMock(return_value=fake_legs)()

    with patch("app.api.routes.public_landing.get_probability_engine") as get_engine:
        get_engine.return_value = FakeEngine()
        resp = await client.get("/api/public/todays-top-picks")
    assert resp.status_code == 200
    data = resp.json()
    assert "picks" in data
    assert "as_of" in data
    assert "date" in data
    assert len(data["picks"]) >= 1
    first = data["picks"][0]
    assert first["sport"] in ("NFL", "NBA", "NHL", "MLB")
    assert first["matchup"]
    assert first["confidence"] >= 0
    assert first["market"] in ("moneyline", "spread", "total")
    assert first["builder_url"].startswith("/app")


@pytest.mark.asyncio
async def test_todays_top_picks_returns_200_empty_when_no_candidates(client: AsyncClient):
    """When the pipeline returns no candidates, endpoint returns 200 with picks=[] (no 500)."""
    import app.api.routes.public_landing as pl
    pl._cache_payload = None
    pl._cache_ts = 0.0
    with patch("app.api.routes.public_landing.get_probability_engine") as get_engine:
        fake = type("E", (), {"get_candidate_legs": lambda **kw: AsyncMock(return_value=[])()})()
        get_engine.return_value = fake
        resp = await client.get("/api/public/todays-top-picks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["picks"] == []
