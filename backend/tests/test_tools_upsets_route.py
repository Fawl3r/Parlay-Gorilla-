from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.main import app
from app.core.access_control import get_optional_user_access
from app.services.tools.upset_finder_response_cache import UpsetFinderResponseCache


class _FakeResult:
    def __init__(self, *, sport: str = "nba", days: int = 7, min_edge: float = 3.0, candidates_count: int = 0):
        self._sport = sport
        self._days = days
        self._min_edge = min_edge
        self._candidates_count = candidates_count

    def to_dict(self):
        return {
            "sport": self._sport,
            "window_days": self._days,
            "min_edge": self._min_edge,
            "generated_at": "2026-01-01T00:00:00Z",
            "candidates": [{}] * self._candidates_count,
            "meta": {"games_scanned": 0, "games_with_odds": 0, "missing_odds": 0, "games_scanned_capped": False},
        }


@pytest.mark.asyncio
async def test_upsets_anon_returns_200_with_access_and_meta(client, monkeypatch):
    # Isolate in-memory cache for determinism
    from app.api.routes import tools as tools_routes
    monkeypatch.setattr(tools_routes, "upset_finder_response_cache", UpsetFinderResponseCache(), raising=True)

    resp = await client.get("/api/tools/upsets?sport=nba&days=7&meta_only=1")
    assert resp.status_code == 200
    data = resp.json()

    assert data["access"]["can_view_candidates"] is False
    assert data["access"]["reason"] == "login_required"
    assert data["candidates"] == []
    assert "meta" in data
    assert isinstance(data["meta"]["games_scanned"], int)
    assert isinstance(data["meta"]["games_with_odds"], int)
    assert isinstance(data["meta"]["missing_odds"], int)


@pytest.mark.asyncio
async def test_upsets_free_returns_200_with_premium_required_access(client, monkeypatch):
    from app.api.routes import tools as tools_routes
    monkeypatch.setattr(tools_routes, "upset_finder_response_cache", UpsetFinderResponseCache(), raising=True)

    async def _free_access():
        return SimpleNamespace(can_use_upset_finder=False)

    original = dict(app.dependency_overrides)
    app.dependency_overrides[get_optional_user_access] = _free_access
    try:
        resp = await client.get("/api/tools/upsets?sport=nba&days=7")
        assert resp.status_code == 200
        data = resp.json()
        assert data["access"]["can_view_candidates"] is False
        assert data["access"]["reason"] == "premium_required"
        assert data["candidates"] == []
        assert "meta" in data
    finally:
        app.dependency_overrides = original


@pytest.mark.asyncio
async def test_upsets_premium_returns_200_with_access_true(client, monkeypatch):
    from app.api.routes import tools as tools_routes
    monkeypatch.setattr(tools_routes, "upset_finder_response_cache", UpsetFinderResponseCache(), raising=True)

    async def _premium_access():
        return SimpleNamespace(can_use_upset_finder=True)

    original = dict(app.dependency_overrides)
    app.dependency_overrides[get_optional_user_access] = _premium_access
    try:
        resp = await client.get("/api/tools/upsets?sport=nba&days=7&min_edge=3&max_results=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["access"]["can_view_candidates"] is True
        assert data["access"]["reason"] is None
        assert "meta" in data
        assert "candidates" in data
    finally:
        app.dependency_overrides = original


@pytest.mark.asyncio
async def test_upsets_cache_hit_and_force_bypass(client, monkeypatch):
    from app.api.routes import tools as tools_routes
    monkeypatch.setattr(tools_routes, "upset_finder_response_cache", UpsetFinderResponseCache(), raising=True)

    async def _premium_access():
        return SimpleNamespace(can_use_upset_finder=True)

    original = dict(app.dependency_overrides)
    app.dependency_overrides[get_optional_user_access] = _premium_access
    try:
        with patch("app.api.routes.tools.UpsetFinderToolsService.find_candidates", new_callable=AsyncMock) as mocked:
            mocked.return_value = _FakeResult(candidates_count=0)

            r1 = await client.get("/api/tools/upsets?sport=nba&days=7&min_edge=3&max_results=20")
            assert r1.status_code == 200
            r2 = await client.get("/api/tools/upsets?sport=nba&days=7&min_edge=3&max_results=20")
            assert r2.status_code == 200

            assert mocked.await_count == 1

            r3 = await client.get("/api/tools/upsets?sport=nba&days=7&min_edge=3&max_results=20&force=1")
            assert r3.status_code == 200
            assert mocked.await_count == 2
    finally:
        app.dependency_overrides = original


@pytest.mark.asyncio
async def test_upsets_meta_only_does_not_compute_candidates_even_for_premium(client, monkeypatch):
    from app.api.routes import tools as tools_routes
    monkeypatch.setattr(tools_routes, "upset_finder_response_cache", UpsetFinderResponseCache(), raising=True)

    async def _premium_access():
        return SimpleNamespace(can_use_upset_finder=True)

    original = dict(app.dependency_overrides)
    app.dependency_overrides[get_optional_user_access] = _premium_access
    try:
        with patch("app.api.routes.tools.UpsetFinderToolsService.scan_meta", new_callable=AsyncMock) as scan_meta:
            scan_meta.return_value = {"games_scanned": 0, "games_with_odds": 0, "missing_odds": 0, "games_scanned_capped": False}
            with patch("app.api.routes.tools.UpsetFinderToolsService.find_candidates", new_callable=AsyncMock) as find_candidates:
                resp = await client.get("/api/tools/upsets?sport=nba&days=7&meta_only=1")
                assert resp.status_code == 200
                assert scan_meta.await_count == 1
                assert find_candidates.await_count == 0
    finally:
        app.dependency_overrides = original

