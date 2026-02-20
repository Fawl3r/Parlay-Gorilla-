"""
Admin model API routes. Never returns 500; DB/table errors return safe fallbacks.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, ProgrammingError
from typing import Optional
from datetime import datetime

from app.core.dependencies import get_db
from app.core.model_config import MODEL_VERSION, SPORT_WEIGHTS, HOME_ADVANTAGE
from app.services.prediction_tracker import PredictionTrackerService
from app.models.user import User
from .auth import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/metrics")
async def get_model_metrics(
    sport: Optional[str] = Query(None, description="Filter by sport (NFL, NBA, etc.)"),
    market_type: Optional[str] = Query(None, description="Filter by market type (moneyline, spread, total)"),
    lookback_days: int = Query(30, ge=1, le=365, description="Days to look back"),
    model_version: Optional[str] = Query(None, description="Filter by model version"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get model accuracy metrics and performance statistics.
    
    Returns:
    - Overall accuracy
    - Brier score (calibration)
    - Average edge
    - Positive edge accuracy (how well we do when we see value)
    """
    try:
        tracker = PredictionTrackerService(db)
        
        stats = await tracker.get_accuracy_stats(
            sport=sport.upper() if sport else None,
            market_type=market_type,
            lookback_days=lookback_days,
            model_version=model_version,
        )
        
        logger.info("admin.endpoint.success", extra={"endpoint": "model.metrics"})
        total = (stats or {}).get("total_predictions", 0) or 0
        return {
            "current_model_version": MODEL_VERSION,
            "model_version": str(MODEL_VERSION) if MODEL_VERSION else "",
            "filters": {
                "sport": sport,
                "market_type": market_type,
                "lookback_days": lookback_days,
                "model_version": model_version,
            },
            "metrics": stats or {},
            "interpretation": {
                "accuracy": _interpret_accuracy((stats.get("accuracy") or 0), total),
                "brier_score": _interpret_brier((stats.get("brier_score") or 0), total),
                "edge_performance": _interpret_edge_performance(
                    stats.get("avg_edge") or 0,
                    stats.get("positive_edge_accuracy") or 0,
                    total,
                ),
            },
        }
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "model.metrics", "error": str(e)}, exc_info=True)
        return {
            "current_model_version": MODEL_VERSION,
            "model_version": str(MODEL_VERSION) if MODEL_VERSION else "",
            "filters": {"sport": sport, "market_type": market_type, "lookback_days": lookback_days, "model_version": model_version},
            "metrics": {},
            "interpretation": {
                "accuracy": "Insufficient data — record and resolve predictions to see accuracy",
                "brier_score": "Insufficient data — resolve predictions to see calibration",
                "edge_performance": "Insufficient data — record +EV predictions and resolve games",
            },
        }


@router.get("/team-biases")
async def get_team_biases(
    sport: str = Query(..., description="Sport code (NFL, NBA, etc.)"),
    min_games: int = Query(10, ge=5, le=100, description="Minimum games for inclusion"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get per-team bias adjustments.
    
    Shows which teams the model consistently over/under-rates
    and the calibration adjustments applied.
    """
    try:
        tracker = PredictionTrackerService(db)
        
        biases = await tracker.get_team_bias_adjustments(sport.upper())
        
        # Sort by absolute bias (most biased first)
        sorted_biases = sorted(
            biases.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        return {
            "sport": sport.upper(),
            "total_teams": len(biases),
            "teams": [
                {
                    "team": team,
                    "bias_adjustment": round(bias, 4),
                    "adjustment_pct": f"{bias * 100:+.2f}%",
                    "direction": "overrated" if bias < 0 else "underrated" if bias > 0 else "calibrated",
                }
                for team, bias in sorted_biases
            ],
            "summary": _summarize_biases(biases),
        }
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "model.team-biases", "error": str(e)}, exc_info=True)
        return {"sport": sport.upper(), "total_teams": 0, "teams": [], "summary": "No data available"}


@router.post("/recalibrate")
async def trigger_recalibration(
    sport: str = Query(..., description="Sport to recalibrate"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Trigger recalibration of team biases for a sport.
    
    This updates the TeamCalibration records based on recent prediction outcomes.
    Should be called periodically (e.g., weekly) via cron job.
    """
    try:
        tracker = PredictionTrackerService(db)
        
        updated_count = await tracker.update_team_calibrations(sport.upper())
        
        return {
            "sport": sport.upper(),
            "teams_updated": updated_count,
            "model_version": MODEL_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "model.recalibrate", "error": str(e)}, exc_info=True)
        return {"sport": sport.upper(), "teams_updated": 0, "model_version": MODEL_VERSION, "timestamp": datetime.utcnow().isoformat(), "error": "Recalibration failed"}


@router.get("/config")
async def get_model_config(
    admin: User = Depends(require_admin),
):
    """Get current model configuration. Never 500."""
    try:
        logger.info("admin.endpoint.success", extra={"endpoint": "model.config"})
        return {
            "model_version": MODEL_VERSION,
            "sport_weights": SPORT_WEIGHTS,
            "home_advantage": HOME_ADVANTAGE,
            "description": "Current Parlay Gorilla prediction model configuration",
        }
    except Exception as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "model.config", "error": str(e)}, exc_info=True)
        return {"model_version": None, "sport_weights": {}, "home_advantage": {}, "description": "Configuration unavailable"}


@router.get("/sports-breakdown")
async def get_sports_breakdown(
    lookback_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get accuracy breakdown by sport. Returns safe empty on errors."""
    try:
        sports = ["NFL", "NBA", "NHL", "MLB", "SOCCER"]
        tracker = PredictionTrackerService(db)
        results = []
        for sport in sports:
            try:
                stats = await tracker.get_accuracy_stats(sport=sport, lookback_days=lookback_days)
                if stats and stats.get("total_predictions", 0) > 0:
                    results.append({"sport": sport, **stats})
            except Exception:
                pass
        results.sort(key=lambda x: x.get("accuracy", 0), reverse=True)
        logger.info("admin.endpoint.success", extra={"endpoint": "model.sports-breakdown"})
        return {
            "model_version": MODEL_VERSION,
            "lookback_days": lookback_days,
            "sports": results,
            "best_performing": results[0]["sport"] if results else None,
        }
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "model.sports-breakdown", "error": str(e)}, exc_info=True)
        return {"model_version": MODEL_VERSION, "lookback_days": lookback_days, "sports": [], "best_performing": None}


@router.get("/market-breakdown")
async def get_market_breakdown(
    sport: Optional[str] = Query(None),
    lookback_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get accuracy breakdown by market type. Returns safe empty on errors."""
    try:
        markets = ["moneyline", "spread", "total"]
        tracker = PredictionTrackerService(db)
        results = []
        for market in markets:
            try:
                stats = await tracker.get_accuracy_stats(
                    sport=sport.upper() if sport else None,
                    market_type=market,
                    lookback_days=lookback_days,
                )
                if stats and stats.get("total_predictions", 0) > 0:
                    results.append({"market_type": market, **stats})
            except Exception:
                pass
        logger.info("admin.endpoint.success", extra={"endpoint": "model.market-breakdown"})
        return {"model_version": MODEL_VERSION, "sport_filter": sport, "lookback_days": lookback_days, "markets": results}
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "model.market-breakdown", "error": str(e)}, exc_info=True)
        return {"model_version": MODEL_VERSION, "sport_filter": sport, "lookback_days": lookback_days, "markets": []}


# Helper functions

def _interpret_accuracy(accuracy: float, total_predictions: int = 0) -> str:
    """Interpret accuracy score. When no data, avoid 'needs improvement'."""
    if total_predictions == 0:
        return "Insufficient data — record and resolve predictions to see accuracy"
    if accuracy >= 0.58:
        return "Excellent - significantly beating 50/50"
    elif accuracy >= 0.54:
        return "Good - beating the breakeven threshold"
    elif accuracy >= 0.52:
        return "Fair - slight edge"
    elif accuracy >= 0.50:
        return "Break-even - no clear edge"
    else:
        return "Below average - model needs improvement"


def _interpret_brier(brier: float, total_predictions: int = 0) -> str:
    """Interpret Brier score (lower is better). When no data, neutral message."""
    if total_predictions == 0:
        return "Insufficient data — resolve predictions to see calibration"
    if brier <= 0.20:
        return "Excellent calibration"
    elif brier <= 0.23:
        return "Good calibration"
    elif brier <= 0.25:
        return "Average calibration"
    else:
        return "Poor calibration - predictions not well-calibrated to outcomes"


def _interpret_edge_performance(avg_edge: float, pos_edge_acc: float, total_predictions: int = 0) -> str:
    """Interpret how well we perform when we find edge. When no data, neutral message."""
    if total_predictions == 0:
        return "Insufficient data — record +EV predictions and resolve games"
    if pos_edge_acc >= 0.56:
        return f"Strong - {pos_edge_acc*100:.0f}% accuracy on +EV plays (avg edge: {avg_edge*100:.1f}%)"
    elif pos_edge_acc >= 0.52:
        return f"Good - {pos_edge_acc*100:.0f}% on +EV plays, profitable long-term"
    else:
        return f"Needs work - {pos_edge_acc*100:.0f}% on +EV plays"


def _summarize_biases(biases: dict) -> str:
    """Summarize team biases"""
    if not biases:
        return "No team calibrations available yet"
    
    overrated = sum(1 for b in biases.values() if b < -0.02)
    underrated = sum(1 for b in biases.values() if b > 0.02)
    calibrated = len(biases) - overrated - underrated
    
    return f"{calibrated} calibrated, {overrated} overrated, {underrated} underrated"

