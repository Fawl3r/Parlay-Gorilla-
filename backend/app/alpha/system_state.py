"""
System learning state for alpha engine: paused / active / degraded.

Used by GET /ops/alpha-engine-status. No fabrication: only returns state from
resolved prediction count, validated features, meta state, and recent errors.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Minimum resolved predictions to consider learning "active"
MINIMUM_RESOLVED_FOR_LEARNING = 200


async def update_alpha_meta_after_job(
    db: AsyncSession,
    *,
    last_feature_discovery_at: bool = False,
    last_alpha_research_at: bool = False,
    last_experiment_eval_at: bool = False,
    system_state: Optional[str] = None,
    last_error: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> None:
    """Update AlphaMetaState after a scheduler job. Creates row if missing."""
    from app.models.alpha_meta_state import AlphaMetaState

    result = await db.execute(select(AlphaMetaState).limit(1))
    row = result.scalars().first()
    now = datetime.now(timezone.utc)
    if not row:
        row = AlphaMetaState(
            learning_paused=False,
            system_state=system_state or "PAUSED",
            last_feature_discovery_at=now if last_feature_discovery_at else None,
            last_alpha_research_at=now if last_alpha_research_at else None,
            last_experiment_eval_at=now if last_experiment_eval_at else None,
            last_error=last_error,
            last_error_at=now if last_error else None,
            correlation_id=correlation_id,
        )
        db.add(row)
    else:
        if last_feature_discovery_at:
            row.last_feature_discovery_at = now
        if last_alpha_research_at:
            row.last_alpha_research_at = now
        if last_experiment_eval_at:
            row.last_experiment_eval_at = now
        if system_state is not None:
            row.system_state = system_state
        if last_error is not None:
            row.last_error = last_error
            row.last_error_at = now
        if correlation_id is not None:
            row.correlation_id = correlation_id
        row.updated_at = now
    await db.commit()


def compute_system_learning_state(
    resolved_predictions: int = 0,
    validated_count: int = 0,
    last_feature_discovery_at: Optional[str] = None,
    last_alpha_research_at: Optional[str] = None,
    last_experiment_eval_at: Optional[str] = None,
    last_error: Optional[str] = None,
    last_error_at: Optional[str] = None,
    learning_paused: bool = False,
    system_state_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute system_learning_state object for the alpha-engine-status endpoint.

    - paused: resolved_predictions < minimum OR no validated features OR learning_paused
    - active: enough samples, jobs running, no recent error
    - degraded: recent error or alpha decay triggered widespread deactivation
    """
    insufficient_samples = resolved_predictions < MINIMUM_RESOLVED_FOR_LEARNING
    no_validated = validated_count < 1

    if system_state_override in ("PAUSED", "ACTIVE", "DEGRADED"):
        state = system_state_override.lower()
    elif learning_paused:
        state = "paused"
        reason = "learning_paused"
    elif insufficient_samples:
        state = "paused"
        reason = "insufficient_samples"
    elif no_validated and not insufficient_samples:
        state = "paused"
        reason = "no_validated_features"
    elif last_error and last_error_at:
        state = "degraded"
        reason = "recent_error"
    else:
        state = "active"
        reason = "ok"

    return {
        "state": state,
        "reason": reason,
        "insufficient_samples": insufficient_samples,
        "last_feature_discovery_at": last_feature_discovery_at,
        "last_alpha_research_at": last_alpha_research_at,
        "last_experiment_eval_at": last_experiment_eval_at,
        "last_error": last_error,
        "last_error_at": last_error_at,
    }
