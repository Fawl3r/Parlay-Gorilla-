"""
Pipeline sanity: insert prediction -> resolve (outcome) -> model health returns non-null.

Prevents silent regressions that bring you back to "0 predictions / N/A accuracy."
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome
from app.services.model_health_service import get_model_health


@pytest.mark.asyncio
async def test_pipeline_sanity_one_resolved_prediction_returns_non_null_metrics(db: AsyncSession):
    """
    Insert one prediction row, resolve it with an outcome, then get_model_health
    returns prediction_count_resolved >= 1 and includes pipeline_ok / pipeline_blockers.
    (Accuracy/brier are only computed when resolved count >= MIN_RESOLVED_FOR_METRICS, so we
    assert the pipeline sees the resolved row and status banner is present.)
    """
    pred_id = uuid.uuid4()
    pred = ModelPrediction(
        id=pred_id,
        sport="nfl",
        home_team="TeamA",
        away_team="TeamB",
        market_type="moneyline",
        team_side="home",
        predicted_prob=0.65,
        model_version="test-1.0",
    )
    db.add(pred)
    db.add(
        PredictionOutcome(
            prediction_id=pred_id,
            was_correct=True,
            error_magnitude=0.1,
            signed_error=0.1,
        )
    )
    await db.commit()

    health = await get_model_health(db)
    assert health["prediction_count_resolved"] >= 1, "resolved count should reflect one outcome"
    assert health["prediction_count_total"] >= 1, "total predictions should include the one we inserted"
    assert "pipeline_ok" in health, "ops status banner must include pipeline_ok"
    assert "pipeline_blockers" in health, "ops status banner must include pipeline_blockers"
    assert isinstance(health["pipeline_blockers"], list), "pipeline_blockers must be a list"
    assert "jobs_stale" in health and isinstance(health["jobs_stale"], bool), "jobs_stale must be bool"
    assert "jobs_stale_reasons" in health and isinstance(health["jobs_stale_reasons"], list), "jobs_stale_reasons must be list"
    assert "unresolved_by_sport" in health and isinstance(health["unresolved_by_sport"], dict), "unresolved_by_sport must be dict"
    assert "oldest_unresolved_created_at" in health
    assert "sample_unresolved_event_ids" in health and isinstance(health["sample_unresolved_event_ids"], list)
    assert "recent_resolution_mismatches_count_24h" in health
