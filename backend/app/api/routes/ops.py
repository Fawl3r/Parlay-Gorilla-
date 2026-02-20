"""Ops endpoints: job status, runbook helpers, public Safety Mode snapshot, model health."""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from app.core import telemetry
from app.core.config import settings
from app.core.safety_mode import get_safety_snapshot
from app.database.session import AsyncSessionLocal
from app.repositories.scheduler_job_run_repository import SchedulerJobRunRepository

router = APIRouter()

OPS_VERIFY_TOKEN = os.environ.get("OPS_VERIFY_TOKEN", "").strip() or getattr(settings, "ops_verify_token", None) or ""


def _require_ops_token(request: Request) -> None:
    """If OPS_VERIFY_TOKEN is set, require header x-ops-token to match. Otherwise no-op (local/dev). Raises 403 on mismatch."""
    if not OPS_VERIFY_TOKEN:
        return
    token = (request.headers.get("x-ops-token") or "").strip()
    if token != OPS_VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="forbidden")


def _get_git_sha() -> str:
    """Return short commit SHA from GIT_SHA env or git rev-parse. Never raises; returns 'unknown' on failure."""
    sha = os.environ.get("GIT_SHA", "").strip()
    if sha:
        return sha
    try:
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


@router.get("/version")
async def ops_version(request: Request):
    """
    Deployment version info for health checks and cutover verification.
    When OPS_VERIFY_TOKEN is set, requires header x-ops-token. Never returns 500.
    """
    _require_ops_token(request)
    git_sha = _get_git_sha()
    build_time = os.environ.get("BUILD_TIME") or datetime.now(timezone.utc).isoformat()
    environment = getattr(settings, "environment", os.environ.get("ENVIRONMENT", "unknown"))
    return JSONResponse(
        content={
            "git_sha": git_sha,
            "build_time": build_time,
            "environment": environment,
            "service": "backend",
        }
    )


@router.get("/verify")
async def ops_verify(request: Request):
    """
    Minimal endpoint for CI/verify_production_sync: returns ok and git_sha.
    Requires x-ops-token when OPS_VERIFY_TOKEN is set. Never returns 500.
    """
    _require_ops_token(request)
    git_sha = _get_git_sha()
    return JSONResponse(content={"ok": True, "git_sha": git_sha})


@router.get("/deploy-status")
async def ops_deploy_status(request: Request):
    """
    Read last successful deploy metadata from last_deploy.json (e.g. /opt/parlaygorilla/last_deploy.json).
    Token-protected like /ops/verify. Never returns 500; returns empty structure if file missing.
    """
    _require_ops_token(request)
    deploy_path = os.environ.get("LAST_DEPLOY_JSON_PATH", "/opt/parlaygorilla/last_deploy.json")
    current_sha = _get_git_sha()
    out = {"current_sha": current_sha, "last_deploy": {}}
    try:
        with open(deploy_path, "r") as f:
            data = json.load(f)
            out["last_deploy"] = data
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return JSONResponse(content=out)


@router.get("/safety")
async def ops_safety(request: Request):
    """Public Safety Mode snapshot (state, reasons, telemetry, events). No auth. For frontend banner."""
    try:
        await telemetry.load_critical_from_redis()
    except Exception:
        pass
    snap = get_safety_snapshot()
    try:
        await telemetry.save_critical_to_redis(snap)
    except Exception:
        pass
    return snap


@router.get("/jobs")
async def ops_jobs(request: Request):
    """
    Last run status for each scheduler job.
    Returns: job_name, last_run_at, duration_ms, status, error_snippet.
    """
    try:
        async with AsyncSessionLocal() as db:
            repo = SchedulerJobRunRepository(db)
            jobs = await repo.get_all()
        body = {"jobs": jobs}
        if hasattr(request, "state") and getattr(request.state, "request_id", None):
            body["request_id"] = request.state.request_id
        return JSONResponse(content=body)
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)[:500],
                "jobs": [],
                "request_id": getattr(request.state, "request_id", None) if hasattr(request, "state") else None,
            },
            status_code=500,
        )


@router.get("/model-health")
async def ops_model_health(request: Request):
    """
    Model health: prediction_count_total, prediction_count_resolved, accuracy,
    brier_score, avg_edge, avg_ev, calibration_last_trained_at, last_resolution_run_at, status.
    Never 500: returns 200 with status INSUFFICIENT_DATA or error key on failure.
    """
    try:
        from app.services.model_health_service import get_model_health
        async with AsyncSessionLocal() as db:
            health = await get_model_health(db)
        return JSONResponse(content=health)
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)[:500],
                "prediction_count_total": 0,
                "prediction_count_resolved": 0,
                "accuracy": None,
                "brier_score": None,
                "avg_edge": None,
                "avg_ev": None,
                "calibration_last_trained_at": None,
                "last_resolution_run_at": None,
                "status": "INSUFFICIENT_DATA",
            },
        )


@router.get("/quant-snapshot")
async def ops_quant_snapshot(request: Request):
    """
    Quant snapshot: prediction_count, resolved_count, avg_clv, accuracy,
    brier_score, calibration_version, last_training_time, model_state.
    """
    try:
        from app.services.model_health_service import get_quant_snapshot
        async with AsyncSessionLocal() as db:
            snapshot = await get_quant_snapshot(db)
        return JSONResponse(content=snapshot)
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)[:500], "model_state": "UNKNOWN"},
            status_code=500,
        )


@router.get("/institutional-health")
async def ops_institutional_health(request: Request):
    """
    Institutional adaptive learning health: model_state, health_score, current_regime,
    strategy_weights, rolling_roi, drawdown, last_rl_update, calibration_version.
    """
    try:
        from app.services.institutional.model_health_service import ModelHealthService
        from app.services.institutional.strategy_decomposition_service import StrategyDecompositionService
        from app.services.institutional.bankroll_manager import BankrollManager
        from app.services.institutional.market_regime_service import MarketRegimeService
        async with AsyncSessionLocal() as db:
            health_svc = ModelHealthService(db)
            strategy_svc = StrategyDecompositionService(db)
            bankroll_svc = BankrollManager(db)
            regime_svc = MarketRegimeService(db)
            state = await health_svc.get_current_state()
            weights = await strategy_svc.get_weights()
            bankroll_metrics = await bankroll_svc.get_metrics()
            current_regime = await regime_svc.detect_regime()
        return JSONResponse(content={
            "model_state": state.get("model_state", "GREEN"),
            "health_score": state.get("health_score"),
            "current_regime": current_regime,
            "strategy_weights": weights,
            "rolling_roi": state.get("rolling_roi"),
            "drawdown": None,
            "bankroll_safety_multiplier": bankroll_metrics.get("bankroll_safety_multiplier"),
            "last_rl_update": state.get("last_rl_update_at"),
            "calibration_version": state.get("calibration_version"),
        })
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)[:500],
                "model_state": "GREEN",
                "health_score": None,
                "current_regime": "UNKNOWN",
                "strategy_weights": {},
            },
            status_code=500,
        )


@router.get("/alpha-engine-status")
async def ops_alpha_engine_status(request: Request):
    """
    Alpha engine status: active_alpha_features, testing_features, validated_features,
    alpha_roi_contribution (null until real P&L attribution), recent_promotions,
    recent_deprecations, system_learning_state object, counts.
    Never returns 500: empty DB yields empty lists and system_learning_state paused.
    """
    import logging
    import uuid
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select, func

    logger = logging.getLogger(__name__)
    correlation_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())

    # alpha_roi_contribution: intentionally null until we have attribution data.
    # TODO: Compute when prediction->bet_sizing->payout attribution exists (e.g. table
    # linking prediction_id to stake/payout or parlay_leg outcome); do not leave null
    # forever once that pipeline exists. Requirement: prediction->bet sizing->payout
    # attribution table (or equivalent) to attribute P&L/ROI to alpha features.
    safe_payload = {
        "active_alpha_features": [],
        "testing_features": [],
        "validated_features": [],
        "alpha_roi_contribution": None,
        "recent_promotions": [],
        "recent_deprecations": [],
        "system_learning_state": {
            "state": "paused",
            "reason": "insufficient_samples",
            "insufficient_samples": True,
            "last_feature_discovery_at": None,
            "last_alpha_research_at": None,
            "last_experiment_eval_at": None,
            "last_error": None,
            "last_error_at": None,
        },
        "counts": {"testing": 0, "validated": 0, "rejected": 0, "deprecated": 0},
    }

    try:
        from app.models.alpha_feature import AlphaFeature
        from app.models.alpha_decay_log import AlphaDecayLog
        from app.models.alpha_meta_state import AlphaMetaState
        from app.services.model_health_service import get_model_health
        from app.alpha.system_state import compute_system_learning_state

        async with AsyncSessionLocal() as db:
            testing_res = await db.execute(select(func.count(AlphaFeature.id)).where(AlphaFeature.status == "TESTING"))
            validated_res = await db.execute(select(func.count(AlphaFeature.id)).where(AlphaFeature.status == "VALIDATED"))
            rejected_res = await db.execute(select(func.count(AlphaFeature.id)).where(AlphaFeature.status == "REJECTED"))
            deprecated_res = await db.execute(select(func.count(AlphaFeature.id)).where(AlphaFeature.status == "DEPRECATED"))
            testing_count = testing_res.scalar() or 0
            validated_count = validated_res.scalar() or 0
            rejected_count = rejected_res.scalar() or 0
            deprecated_count = deprecated_res.scalar() or 0

            counts = {"testing": testing_count, "validated": validated_count, "rejected": rejected_count, "deprecated": deprecated_count}
            safe_payload["counts"] = counts

            active_res = await db.execute(
                select(AlphaFeature.feature_name).where(
                    AlphaFeature.status == "VALIDATED",
                    AlphaFeature.deprecated_at.is_(None),
                )
            )
            safe_payload["active_alpha_features"] = [r[0] for r in active_res.scalars().all() if r[0]]

            testing_names = await db.execute(select(AlphaFeature.feature_name).where(AlphaFeature.status == "TESTING"))
            safe_payload["testing_features"] = [r[0] for r in testing_names.scalars().all() if r[0]]

            validated_names = await db.execute(select(AlphaFeature.feature_name).where(AlphaFeature.status == "VALIDATED"))
            safe_payload["validated_features"] = [r[0] for r in validated_names.scalars().all() if r[0]]

            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            promos = await db.execute(
                select(AlphaFeature.feature_name, AlphaFeature.validated_at)
                .where(AlphaFeature.status == "VALIDATED", AlphaFeature.validated_at >= cutoff)
                .order_by(AlphaFeature.validated_at.desc())
                .limit(10)
            )
            safe_payload["recent_promotions"] = [
                {"feature_name": r[0], "promoted_at": r[1].isoformat() if r[1] else None}
                for r in promos.scalars().all()
            ]

            decay_res = await db.execute(
                select(AlphaDecayLog.feature_name, AlphaDecayLog.created_at)
                .order_by(AlphaDecayLog.created_at.desc())
                .limit(10)
            )
            safe_payload["recent_deprecations"] = [
                {"feature_name": r[0], "deprecated_at": r[1].isoformat() if r[1] else None}
                for r in decay_res.scalars().all()
            ]

            health = await get_model_health(db)
            resolved_predictions = health.get("prediction_count_resolved") or health.get("resolved_count") or 0

            meta_res = await db.execute(select(AlphaMetaState).limit(1))
            meta_row = meta_res.scalars().first()
            last_fd = getattr(meta_row, "last_feature_discovery_at", None)
            last_ar = getattr(meta_row, "last_alpha_research_at", None)
            last_ee = getattr(meta_row, "last_experiment_eval_at", None)
            last_err = getattr(meta_row, "last_error", None)
            last_err_at = getattr(meta_row, "last_error_at", None)
            learning_paused = bool(getattr(meta_row, "learning_paused", False))
            system_state_override = getattr(meta_row, "system_state", None)

            safe_payload["system_learning_state"] = compute_system_learning_state(
                resolved_predictions=resolved_predictions,
                validated_count=validated_count,
                last_feature_discovery_at=last_fd.isoformat() if last_fd else None,
                last_alpha_research_at=last_ar.isoformat() if last_ar else None,
                last_experiment_eval_at=last_ee.isoformat() if last_ee else None,
                last_error=last_err,
                last_error_at=last_err_at.isoformat() if last_err_at else None,
                learning_paused=learning_paused,
                system_state_override=system_state_override,
            )
    except Exception as e:
        safe_payload["system_learning_state"]["state"] = "paused"
        safe_payload["system_learning_state"]["reason"] = "error"
        safe_payload["system_learning_state"]["last_error"] = str(e)[:500]
        safe_payload["system_learning_state"]["last_error_at"] = datetime.now(timezone.utc).isoformat()
        logger.warning("alpha_engine_status error: %s", e, exc_info=True)

    logger.info(
        "alpha_engine_status",
        extra={
            "correlation_id": correlation_id,
            "counts": safe_payload["counts"],
            "system_learning_state": safe_payload["system_learning_state"],
        },
    )
    return JSONResponse(content=safe_payload)
