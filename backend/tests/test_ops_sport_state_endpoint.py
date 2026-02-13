"""Tests for GET /ops/sport-state/{sport_code} debug endpoint."""

from __future__ import annotations

from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.game import Game
from tests.ugie_fixtures import fixed_test_now


@pytest.mark.asyncio
async def test_ops_sport_state_disabled_returns_404(client: AsyncClient, monkeypatch):
    """When OPS_DEBUG_ENABLED is false, GET /ops/sport-state/{sport_code} returns 404."""
    monkeypatch.setenv("OPS_DEBUG_ENABLED", "false")
    get_settings.cache_clear()
    try:
        resp = await client.get("/ops/sport-state/nfl")
        assert resp.status_code == 404
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_ops_sport_state_unknown_sport_returns_404(client: AsyncClient, monkeypatch):
    """Unknown sport_code returns 404 even when debug is enabled."""
    monkeypatch.setenv("OPS_DEBUG_ENABLED", "true")
    get_settings.cache_clear()
    try:
        resp = await client.get("/ops/sport-state/invalid_sport_xyz_123")
        assert resp.status_code == 404
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_ops_sport_state_postseason_game_returns_postseason_and_window(
    client: AsyncClient,
    db: AsyncSession,
    monkeypatch,
):
    """Known sport with postseason game in in-season window -> POSTSEASON and listing window set."""
    now = fixed_test_now()
    future = now + timedelta(days=3)
    db.add(
        Game(
            external_game_id="ops-debug-postseason-1",
            sport="NFL",
            home_team="KC",
            away_team="BUF",
            start_time=future,
            status="scheduled",
            season_phase="postseason",
            stage="Playoffs",
        )
    )
    await db.commit()

    monkeypatch.setenv("OPS_DEBUG_ENABLED", "true")
    get_settings.cache_clear()
    try:
        resp = await client.get("/ops/sport-state/nfl")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sport_code"] == "NFL"
        assert data["sport_state"]["sport_state"] == "POSTSEASON"
        assert data["sport_state"]["is_enabled"] is True
        assert data["decision_inputs"]["upcoming_postseason_soon_count"] >= 1
        assert data["listing_window"]["window_start_utc"] is not None
        assert data["listing_window"]["window_end_utc"] is not None
        assert "OFFSEASON_NONE" not in data["listing_window"]["window_reason"]
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_ops_sport_state_requires_token_when_set(client: AsyncClient, monkeypatch):
    """When OPS_DEBUG_TOKEN is set, missing or wrong X-Ops-Token returns 403."""
    monkeypatch.setenv("OPS_DEBUG_ENABLED", "true")
    monkeypatch.setenv("OPS_DEBUG_TOKEN", "secret-ops-token")
    get_settings.cache_clear()
    try:
        resp = await client.get("/ops/sport-state/nfl")
        assert resp.status_code == 403
        resp2 = await client.get(
            "/ops/sport-state/nfl",
            headers={"X-Ops-Token": "wrong-token"},
        )
        assert resp2.status_code == 403
        resp3 = await client.get(
            "/ops/sport-state/nfl",
            headers={"X-Ops-Token": "secret-ops-token"},
        )
        assert resp3.status_code == 200
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_ops_sport_state_far_future_only_returns_offseason_and_null_window(
    client: AsyncClient,
    db: AsyncSession,
    monkeypatch,
):
    """Known sport with only far-future game -> OFFSEASON and listing window null."""
    now = fixed_test_now()
    far_future = now + timedelta(days=400)  # beyond sanity window
    db.add(
        Game(
            external_game_id="ops-debug-far-1",
            sport="NBA",
            home_team="LAL",
            away_team="BOS",
            start_time=far_future,
            status="scheduled",
        )
    )
    await db.commit()

    monkeypatch.setenv("OPS_DEBUG_ENABLED", "true")
    get_settings.cache_clear()
    try:
        resp = await client.get("/ops/sport-state/nba")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sport_code"] == "NBA"
        assert data["sport_state"]["sport_state"] == "OFFSEASON"
        assert data["sport_state"]["is_enabled"] is False
        assert data["listing_window"]["window_start_utc"] is None
        assert data["listing_window"]["window_end_utc"] is None
        assert data["listing_window"]["window_reason"] == "OFFSEASON_NONE"
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_ops_route_has_no_store_headers(client: AsyncClient, monkeypatch):
    """All /ops routes return Cache-Control: no-store and Pragma: no-cache (debug safety)."""
    monkeypatch.setenv("OPS_DEBUG_ENABLED", "true")
    get_settings.cache_clear()
    try:
        res = await client.get("/ops/sport-state/nfl")
        assert res.status_code == 200
        assert "no-store" in res.headers.get("Cache-Control", "")
        assert res.headers.get("Pragma") == "no-cache"
    finally:
        get_settings.cache_clear()
