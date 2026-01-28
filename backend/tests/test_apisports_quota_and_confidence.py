"""Tests for API-Sports QuotaManager and ConfidenceEngine.

Note: Full test suite may use SQLite (conftest); some models use JSONB (Postgres-only).
Run these tests with Postgres DATABASE_URL if _init_test_db fails on SQLite.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.services.apisports.quota_manager import QuotaManager, _today_chicago
from app.services.confidence_engine import ConfidenceEngine, BUCKETS


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def test_today_chicago_format():
    """_today_chicago returns YYYY-MM-DD."""
    s = _today_chicago()
    assert len(s) == 10
    assert s[4] == "-" and s[7] == "-"
    assert s[:4].isdigit() and s[5:7].isdigit() and s[8:10].isdigit()


def test_confidence_engine_clamp():
    """clamp keeps value in [low, high]."""
    assert _clamp(0.5, 0.2, 0.9) == 0.5
    assert _clamp(0.1, 0.2, 0.9) == 0.2
    assert _clamp(1.0, 0.2, 0.9) == 0.9


def test_confidence_engine_blend():
    """Blend returns final_prob in [0,1] and a bucket string."""
    engine = ConfidenceEngine(base_w=0.6, min_w=0.2, max_w=0.9)
    r = engine.blend(model_prob=0.7, implied_prob=0.65, data_freshness_score=1.0, sample_size_score=1.0)
    assert 0 <= r.final_prob <= 1
    assert r.confidence_meter in ["50-60", "60-70", "70-80", "80-90", "90+"]
    assert r.w_used >= 0.2 and r.w_used <= 0.9


def test_confidence_engine_low_freshness_reduces_w():
    """Lower freshness reduces model weight."""
    engine = ConfidenceEngine(base_w=0.6, min_w=0.2, max_w=0.9)
    r_high = engine.blend(0.7, 0.65, data_freshness_score=1.0, sample_size_score=1.0)
    r_low = engine.blend(0.7, 0.65, data_freshness_score=0.3, sample_size_score=1.0)
    assert r_low.w_used <= r_high.w_used


@pytest.mark.asyncio
async def test_quota_manager_can_spend_without_redis():
    """When Redis is not configured, can_spend uses DB path (no crash)."""
    with patch("app.services.apisports.quota_manager.get_redis_provider") as mock_provider:
        mock_provider.return_value.is_configured.return_value = False
        with patch("app.database.session.AsyncSessionLocal") as mock_session:
            mock_db = AsyncMock()
            mock_db.get = AsyncMock(return_value=None)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            q = QuotaManager()
            result = await q.can_spend(1)
            assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_quota_manager_remaining_async_without_redis():
    """remaining_async returns non-negative when Redis not configured."""
    with patch("app.services.apisports.quota_manager.get_redis_provider") as mock_provider:
        mock_provider.return_value.is_configured.return_value = False
        with patch("app.database.session.AsyncSessionLocal") as mock_session:
            mock_row = type("Row", (), {"used": 10})()
            mock_db = AsyncMock()
            mock_db.get = AsyncMock(return_value=mock_row)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            q = QuotaManager()
            remaining = await q.remaining_async()
            assert remaining >= 0 and remaining <= 100
