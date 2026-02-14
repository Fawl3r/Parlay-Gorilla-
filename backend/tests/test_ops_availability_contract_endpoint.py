"""Tests for GET /ops/availability-contract."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.api.routes.ops_availability_contract_routes import _build_and_validate
from app.core.config import get_settings


@pytest.mark.asyncio
async def test_availability_contract_disabled_returns_404(client: AsyncClient, monkeypatch):
    """OPS_DEBUG_ENABLED=false -> 404."""
    monkeypatch.setenv("OPS_DEBUG_ENABLED", "false")
    get_settings.cache_clear()
    try:
        resp = await client.get("/ops/availability-contract")
        assert resp.status_code == 404
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_availability_contract_requires_token_when_set(client: AsyncClient, monkeypatch):
    """OPS_DEBUG_TOKEN set and missing/wrong X-Ops-Token -> 403."""
    monkeypatch.setenv("OPS_DEBUG_ENABLED", "true")
    monkeypatch.setenv("OPS_DEBUG_TOKEN", "secret-ops-token")
    get_settings.cache_clear()
    try:
        resp = await client.get("/ops/availability-contract")
        assert resp.status_code == 403
        resp2 = await client.get(
            "/ops/availability-contract",
            headers={"X-Ops-Token": "wrong-token"},
        )
        assert resp2.status_code == 403
        resp3 = await client.get(
            "/ops/availability-contract",
            headers={"X-Ops-Token": "secret-ops-token"},
        )
        assert resp3.status_code == 200
        data = resp3.json()
        assert data.get("ok") is True
        assert "checked_at_utc" in data
        assert "counts" in data
        assert "issues" in data
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_availability_contract_valid_returns_ok(client: AsyncClient, monkeypatch):
    """Debug enabled, valid sports list -> 200, ok=true."""
    monkeypatch.setenv("OPS_DEBUG_ENABLED", "true")
    get_settings.cache_clear()
    try:
        resp = await client.get("/ops/availability-contract")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert "checked_at_utc" in data
        assert data["counts"]["sports"] >= 0
        assert "enabled" in data["counts"]
        assert "disabled" in data["counts"]
        assert data["issues"]["missing_required"] == []
        assert data["issues"]["type_errors"] == []
        assert data["issues"]["duplicate_slugs"] == []
        assert len(data["sports_sample"]) <= 3
    finally:
        get_settings.cache_clear()


def test_build_and_validate_ok():
    """_build_and_validate with valid items -> ok=true."""
    items = [
        {"slug": "nfl", "sport_state": "OFFSEASON", "is_enabled": False, "next_game_at": None},
        {"slug": "nba", "sport_state": "IN_SEASON", "is_enabled": True},
    ]
    ok, issues = _build_and_validate(items)
    assert ok is True
    assert not issues["missing_required"]
    assert not issues["type_errors"]


def test_build_and_validate_missing_required():
    """_build_and_validate with missing is_enabled -> ok=false, issues present."""
    items = [
        {"slug": "nfl", "sport_state": "OFFSEASON"},  # missing is_enabled
    ]
    ok, issues = _build_and_validate(items)
    assert ok is False
    assert len(issues["missing_required"]) >= 1
    assert any("is_enabled" in m.get("missing", []) for m in issues["missing_required"])


def test_build_and_validate_type_error():
    """_build_and_validate with is_enabled as string -> ok=false, type_errors."""
    items = [
        {"slug": "nfl", "sport_state": "OFFSEASON", "is_enabled": "true"},
    ]
    ok, issues = _build_and_validate(items)
    assert ok is False
    assert len(issues["type_errors"]) >= 1


def test_build_and_validate_duplicate_slugs():
    """_build_and_validate with duplicate slug -> ok=false, duplicate_slugs."""
    items = [
        {"slug": "nfl", "sport_state": "OFFSEASON", "is_enabled": False},
        {"slug": "NFL", "sport_state": "IN_SEASON", "is_enabled": True},
    ]
    ok, issues = _build_and_validate(items)
    assert ok is False
    assert "nfl" in issues["duplicate_slugs"]


def test_build_and_validate_sport_state_case_insensitive():
    """sport_state is normalized to upper; lowercase/mixed case accepted."""
    items = [
        {"slug": "nfl", "sport_state": "offseason", "is_enabled": False},
        {"slug": "nba", "sport_state": "In_Season", "is_enabled": True},
    ]
    ok, issues = _build_and_validate(items)
    assert ok is True
    assert not issues["unknown_sport_state_values"]
