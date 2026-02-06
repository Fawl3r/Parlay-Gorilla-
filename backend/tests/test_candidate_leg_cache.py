"""Tests for candidate-legs cache (Redis + in-memory fallback)."""

from __future__ import annotations

import asyncio
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.probability_engine_impl.candidate_leg_cache import (
    CandidateLegCache,
    build_candidate_legs_cache_key,
    get_candidate_leg_cache,
)


def _memory_only_cache() -> CandidateLegCache:
    """Cache that only uses in-memory backend (no Redis)."""
    provider = MagicMock()
    provider.is_configured.return_value = False
    return CandidateLegCache(provider=provider)


def test_build_candidate_legs_cache_key():
    key = build_candidate_legs_cache_key(
        sport="NFL",
        date_utc="2025-02-06",
        week=5,
        include_player_props=False,
    )
    assert "candidate_legs:v1:" in key
    assert "NFL" in key
    assert "2025-02-06" in key
    assert "5" in key
    assert "0" in key

    key_all = build_candidate_legs_cache_key(
        sport="NBA",
        date_utc="2025-02-06",
        week=None,
        include_player_props=True,
    )
    assert "all" in key_all
    assert "1" in key_all


@pytest.mark.asyncio
async def test_cache_set_then_get_returns_value():
    """Cache hit: set then get returns the list."""
    cache = _memory_only_cache()
    key = build_candidate_legs_cache_key(
        sport="NFL",
        date_utc=date.today().isoformat(),
        week=None,
        include_player_props=False,
    )
    value = [
        {"game_id": "1", "confidence_score": 70.0},
        {"game_id": "2", "confidence_score": 60.0},
    ]
    await cache.set(key, value, ttl_seconds=60)
    got = await cache.get(key)
    assert got == value


@pytest.mark.asyncio
async def test_cache_get_miss_returns_none():
    """Cache miss: unknown key returns None."""
    cache = _memory_only_cache()
    got = await cache.get("candidate_legs:v1:nonexistent:2025-02-06:all:0")
    assert got is None


@pytest.mark.asyncio
async def test_cache_ttl_expiry_returns_none():
    """After TTL expires, get returns None (in-memory fallback)."""
    cache = _memory_only_cache()
    key = build_candidate_legs_cache_key(
        sport="NFL",
        date_utc=date.today().isoformat(),
        week=None,
        include_player_props=False,
    )
    await cache.set(key, [{"x": 1}], ttl_seconds=1)
    assert await cache.get(key) is not None
    await asyncio.sleep(1.2)
    assert await cache.get(key) is None


@pytest.mark.asyncio
async def test_get_candidate_legs_cache_hit_bypasses_build(db):
    """When cache returns a list, get_candidate_legs returns it (capped) without running the full pipeline."""
    from app.services.probability_engine_impl.candidate_leg_service import CandidateLegService

    cached_legs = [
        {"game_id": "1", "confidence_score": 80.0, "market_type": "h2h"},
        {"game_id": "2", "confidence_score": 70.0, "market_type": "h2h"},
        {"game_id": "3", "confidence_score": 60.0, "market_type": "h2h"},
    ]
    mock_cache = _memory_only_cache()
    today = date.today().isoformat()
    key = build_candidate_legs_cache_key(
        sport="NFL",
        date_utc=today,
        week=None,
        include_player_props=False,
    )
    await mock_cache.set(key, cached_legs, ttl_seconds=45)

    class _EngineStub:
        sport_code = "NFL"
        def __init__(self, db):
            self.db = db

    with patch("app.services.probability_engine_impl.candidate_leg_service.get_candidate_leg_cache", return_value=mock_cache):
        service = CandidateLegService(engine=_EngineStub(db), repo=AsyncMock())
        legs = await service.get_candidate_legs(
            sport="NFL",
            min_confidence=0.0,
            max_legs=2,
            week=None,
        )
    assert len(legs) == 2
    assert legs[0]["confidence_score"] == 80.0
    assert legs[1]["confidence_score"] == 70.0
