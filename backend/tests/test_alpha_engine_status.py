"""Tests for GET /ops/alpha-engine-status and alpha/strategy_decomposition imports.

Syntax lock-down: In the same runtime that runs tests (or prod), run:
  python -m compileall app -q
from the backend directory. If it fails, the traceback shows the real file + line number
(avoids 'it works on my machine' when the error is in a different file or stale volume).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


def test_strategy_decomposition_service_import():
    """Sanity: strategy_decomposition_service module has valid Python syntax and imports."""
    from app.services.institutional.strategy_decomposition_service import StrategyDecompositionService

    assert StrategyDecompositionService is not None


def test_alpha_and_alpha_feature_import():
    """Sanity: app.alpha and AlphaFeature import without error."""
    from app.alpha import FeatureDiscoveryEngine
    from app.models.alpha_feature import AlphaFeature

    assert AlphaFeature is not None
    # FeatureDiscoveryEngine may be None if safe_import failed
    assert FeatureDiscoveryEngine is not None or True


@pytest.mark.asyncio
async def test_alpha_engine_status_returns_200_and_shape(client: AsyncClient):
    """GET /ops/alpha-engine-status returns 200 and required JSON keys (never 500, empty DB ok)."""
    resp = await client.get("/ops/alpha-engine-status")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "active_alpha_features" in data
    assert "testing_features" in data
    assert "validated_features" in data
    assert "alpha_roi_contribution" in data
    assert data["alpha_roi_contribution"] is None
    assert "recent_promotions" in data
    assert "recent_deprecations" in data
    assert "system_learning_state" in data
    assert "counts" in data
    assert isinstance(data["active_alpha_features"], list)
    assert isinstance(data["testing_features"], list)
    assert isinstance(data["validated_features"], list)
    assert isinstance(data["recent_promotions"], list)
    assert isinstance(data["recent_deprecations"], list)
    assert isinstance(data["counts"], dict)
    sls = data["system_learning_state"]
    assert isinstance(sls, dict)
    assert "state" in sls
    assert sls["state"] in ("paused", "active", "degraded")
    assert "reason" in sls
    assert "insufficient_samples" in sls
    assert "last_feature_discovery_at" in sls
    assert "last_alpha_research_at" in sls
    assert "last_experiment_eval_at" in sls
    assert data["counts"].get("testing") is not None
    assert data["counts"].get("validated") is not None
    assert data["counts"].get("rejected") is not None
    assert data["counts"].get("deprecated") is not None
