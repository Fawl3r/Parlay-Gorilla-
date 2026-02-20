"""
Model health and quant snapshot for ops and admin.

Provides prediction_count, resolved_count, accuracy, Brier score,
calibration status, last_training_time for GET /ops/model-health and GET /ops/quant-snapshot.
Includes pipeline_ok and pipeline_blockers for ops status banner.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome
from app.repositories.scheduler_job_run_repository import SchedulerJobRunRepository

logger = logging.getLogger(__name__)

MIN_RESOLVED_FOR_OK = 30
RESOLVER_STALE_HOURS = 2  # Consider pipeline blocked if result_resolution hasn't run in this many hours


def _compute_pipeline_blockers(
    prediction_count_resolved: int,
    last_resolution_run_at: str | None,
) -> List[str]:
    """Blockers for ops status banner: no resolved data, or resolver not running recently."""
    blockers: List[str] = []
    if prediction_count_resolved < 1:
        blockers.append("no resolved predictions")
    if last_resolution_run_at:
        try:
            # last_resolution_run_at is ISO string from DB
            last = datetime.fromisoformat(last_resolution_run_at.replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - last) > timedelta(hours=RESOLVER_STALE_HOURS):
                blockers.append("result_resolution has not run in 2 hours")
        except Exception:
            pass
    else:
        blockers.append("result_resolution has not run")
    return blockers


async def _unresolved_older_than(db: AsyncSession, hours: int) -> int:
    """Count unresolved predictions with created_at older than given hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    r = await db.execute(
        select(func.count(ModelPrediction.id))
        .where(ModelPrediction.is_resolved == "false")
        .where(ModelPrediction.created_at < cutoff)
    )
    return r.scalar() or 0


def _jobs_stale_and_reasons(
    last_resolution_run_at: str | None,
) -> tuple[bool, List[str]]:
    """True if resolver hasn't run in >2 hours; reasons list for alerting."""
    reasons: List[str] = []
    if not last_resolution_run_at:
        return True, ["result_resolution has not run"]
    try:
        last = datetime.fromisoformat(last_resolution_run_at.replace("Z", "+00:00"))
        if (datetime.now(timezone.utc) - last) > timedelta(hours=RESOLVER_STALE_HOURS):
            reasons.append("result_resolution has not run in 2 hours")
            return True, reasons
    except Exception:
        reasons.append("result_resolution last run time invalid")
        return True, reasons
    return False, reasons


async def _resolver_mismatch_breakdown(db: AsyncSession) -> Dict[str, Any]:
    """Unresolved by sport, oldest created_at, sample event_ids. Fast, cheap queries."""
    # unresolved_by_sport: { sport: count }
    by_sport = await db.execute(
        select(ModelPrediction.sport, func.count(ModelPrediction.id))
        .where(ModelPrediction.is_resolved == "false")
        .group_by(ModelPrediction.sport)
    )
    unresolved_by_sport = {row[0]: row[1] for row in by_sport.all() if row[0]}

    # oldest_unresolved_created_at
    oldest = await db.execute(
        select(func.min(ModelPrediction.created_at)).where(ModelPrediction.is_resolved == "false")
    )
    oldest_ts = oldest.scalar()
    oldest_unresolved_created_at = oldest_ts.isoformat() if oldest_ts else None

    # sample_unresolved_event_ids (top 10 by oldest first)
    sample = await db.execute(
        select(ModelPrediction.game_id)
        .where(ModelPrediction.is_resolved == "false")
        .order_by(ModelPrediction.created_at.asc())
        .limit(10)
    )
    sample_unresolved_event_ids = [str(row[0]) for row in sample.all() if row[0] is not None]

    # recent_resolution_mismatches_count_24h: requires run history (we only store last run per job).
    # Set to 0 until we have per-run history; can wire from run_stats or a run_log table later.
    recent_resolution_mismatches_count_24h = 0

    return {
        "unresolved_by_sport": unresolved_by_sport,
        "oldest_unresolved_created_at": oldest_unresolved_created_at,
        "sample_unresolved_event_ids": sample_unresolved_event_ids,
        "recent_resolution_mismatches_count_24h": recent_resolution_mismatches_count_24h,
    }


async def get_model_health(db: AsyncSession) -> Dict[str, Any]:
    """
    Aggregate model health for GET /ops/model-health.
    Returns: prediction_count_total, prediction_count_resolved, accuracy, brier_score,
    avg_edge, avg_ev, calibration_last_trained_at, last_resolution_run_at, status,
    pipeline_ok, pipeline_blockers, unresolved_predictions_older_than_24h, unresolved_predictions_older_than_7d.
    """
    try:
        total_result = await db.execute(select(func.count(ModelPrediction.id)))
        prediction_count_total = total_result.scalar() or 0

        resolved_result = await db.execute(
            select(func.count(ModelPrediction.id))
            .join(PredictionOutcome, PredictionOutcome.prediction_id == ModelPrediction.id)
        )
        prediction_count_resolved = resolved_result.scalar() or 0

        unresolved_24h = await _unresolved_older_than(db, 24)
        unresolved_7d = await _unresolved_older_than(db, 7 * 24)

        from app.services.prediction_tracker import PredictionTrackerService
        tracker = PredictionTrackerService(db)
        stats = await tracker.get_accuracy_stats()

        accuracy = stats.get("accuracy")
        brier_score = stats.get("brier_score")
        avg_edge = stats.get("avg_edge")
        avg_ev = stats.get("avg_ev")

        calibration_last_trained_at = await _calibration_last_trained_at(db)
        last_resolution_run_at = await _last_job_run_at(db, "result_resolution")

        if prediction_count_resolved < MIN_RESOLVED_FOR_OK:
            status = "INSUFFICIENT_DATA"
        elif accuracy is not None and brier_score is not None:
            if accuracy >= 0.52 and (brier_score or 1) <= 0.26:
                status = "OK"
            else:
                status = "DEGRADED"
        else:
            status = "INSUFFICIENT_DATA"

        pipeline_blockers = _compute_pipeline_blockers(prediction_count_resolved, last_resolution_run_at)
        jobs_stale, jobs_stale_reasons = _jobs_stale_and_reasons(last_resolution_run_at)
        resolver_breakdown = await _resolver_mismatch_breakdown(db)

        out = {
            "prediction_count_total": prediction_count_total,
            "prediction_count_resolved": prediction_count_resolved,
            "accuracy": accuracy,
            "brier_score": brier_score,
            "avg_edge": avg_edge,
            "avg_ev": avg_ev,
            "calibration_last_trained_at": calibration_last_trained_at,
            "last_resolution_run_at": last_resolution_run_at,
            "status": status,
            "pipeline_ok": len(pipeline_blockers) == 0,
            "pipeline_blockers": pipeline_blockers,
            "unresolved_predictions_older_than_24h": unresolved_24h,
            "unresolved_predictions_older_than_7d": unresolved_7d,
            "jobs_stale": jobs_stale,
            "jobs_stale_reasons": jobs_stale_reasons,
            **resolver_breakdown,
        }
        logger.info(
            "admin_metrics_computed",
            extra={
                "prediction_count_total": prediction_count_total,
                "prediction_count_resolved": prediction_count_resolved,
                "status": status,
            },
        )
        return out
    except Exception as e:
        logger.warning("[ModelHealth] get_model_health failed: %s", e)
        return {
            "prediction_count_total": 0,
            "prediction_count_resolved": 0,
            "accuracy": None,
            "brier_score": None,
            "avg_edge": None,
            "avg_ev": None,
            "calibration_last_trained_at": None,
            "last_resolution_run_at": None,
            "status": "INSUFFICIENT_DATA",
            "pipeline_ok": False,
            "pipeline_blockers": ["no resolved predictions", "result_resolution has not run"],
            "unresolved_predictions_older_than_24h": 0,
            "unresolved_predictions_older_than_7d": 0,
            "jobs_stale": True,
            "jobs_stale_reasons": ["result_resolution has not run"],
            "unresolved_by_sport": {},
            "oldest_unresolved_created_at": None,
            "sample_unresolved_event_ids": [],
            "recent_resolution_mismatches_count_24h": 0,
        }


async def _calibration_last_trained_at(db: AsyncSession) -> str | None:
    """Latest trained_at from calibration_bins if table exists."""
    try:
        from app.models.calibration_bin import CalibrationBin
        r = await db.execute(
            select(func.max(CalibrationBin.trained_at)).select_from(CalibrationBin)
        )
        t = r.scalar()
        return t.isoformat() if t else None
    except Exception:
        return None


async def _last_job_run_at(db: AsyncSession, job_name: str) -> str | None:
    """Last run timestamp for a scheduler job from scheduler_job_runs."""
    try:
        repo = SchedulerJobRunRepository(db)
        jobs = await repo.get_all()
        for j in jobs:
            if j.get("job_name") == job_name:
                return j.get("last_run_at")
        return None
    except Exception:
        return None


async def get_quant_snapshot(db: AsyncSession) -> Dict[str, Any]:
    """
    Quant snapshot for GET /ops/quant-snapshot.
    Returns: prediction_count, resolved_count, avg_clv, accuracy, brier_score,
    calibration_version, last_training_time, model_state.
    """
    health = await get_model_health(db)
    health["prediction_count"] = health.get("prediction_count_total", 0)
    health["resolved_count"] = health.get("prediction_count_resolved", 0)
    health["avg_clv"] = None
    health["last_training_time"] = health.get("calibration_last_trained_at")
    health["calibration_status"] = "trained" if health.get("calibration_last_trained_at") else "not_trained"
    health["calibration_version"] = "v1" if health.get("calibration_last_trained_at") else None
    acc = health.get("accuracy")
    brier = health.get("brier_score")
    if acc is not None and brier is not None:
        if acc >= 0.55 and brier <= 0.23:
            health["model_state"] = "GREEN"
        elif acc >= 0.50 and brier <= 0.26:
            health["model_state"] = "YELLOW"
        else:
            health["model_state"] = "RED"
    else:
        health["model_state"] = "UNKNOWN"
    return health


def _get_calibration_model_path() -> Path:
    import os
    path = os.environ.get("CALIBRATION_MODEL_PATH", "data/calibration_model.joblib")
    return Path(path)
