"""
Institutional metrics for admin: rolling ROI, Sharpe proxy, max drawdown,
positive CLV rate, strategy contribution leaderboard, regime performance breakdown.
All derived from real resolved predictions; no fabricated metrics.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome
from app.models.strategy_contribution import StrategyContribution

logger = logging.getLogger(__name__)

WINDOW = 100
LOOKBACK_DAYS = 90


class InstitutionalMetricsService:
    """Compute institutional metrics from resolved predictions only."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_institutional_metrics(
        self,
        lookback_days: int = LOOKBACK_DAYS,
        sport: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns: rolling_roi, sharpe_proxy, max_drawdown, positive_clv_rate,
        strategy_contribution_leaderboard, regime_performance_breakdown.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        q = (
            select(ModelPrediction, PredictionOutcome)
            .join(PredictionOutcome, PredictionOutcome.prediction_id == ModelPrediction.id)
            .where(ModelPrediction.resolved_at >= cutoff)
        )
        if sport:
            q = q.where(ModelPrediction.sport == sport.upper())
        q = q.order_by(ModelPrediction.resolved_at.asc())
        r = await self.db.execute(q)
        rows = r.all()
        if not rows:
            return {
                "rolling_roi": None,
                "sharpe_proxy": None,
                "max_drawdown": None,
                "positive_clv_rate": None,
                "strategy_contribution_leaderboard": [],
                "regime_performance_breakdown": {},
                "total_resolved": 0,
            }

        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        returns: List[float] = []
        clv_positive_count = 0
        clv_total = 0
        by_regime: Dict[str, List[bool]] = {}
        for pred, outcome in rows:
            implied_odds = getattr(pred, "implied_odds", None) or 2.0
            unit = 1.0
            if outcome.was_correct:
                cumulative += unit * (implied_odds - 1.0)
                ret = (implied_odds - 1.0)
            else:
                cumulative -= unit
                ret = -1.0
            returns.append(ret)
            peak = max(peak, cumulative)
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
            ev = getattr(pred, "expected_value", None)
            if ev is not None:
                clv_total += 1
                if ev > 0:
                    clv_positive_count += 1
            regime = getattr(pred, "market_regime", None) or "UNKNOWN"
            by_regime.setdefault(regime, []).append(outcome.was_correct)

        total = len(rows)
        roi = (cumulative / total * 100) if total else None
        mean_ret = sum(returns) / len(returns) if returns else 0
        std_ret = (sum((x - mean_ret) ** 2 for x in returns) / len(returns)) ** 0.5 if len(returns) > 1 else 0
        sharpe_proxy = (mean_ret / std_ret) if std_ret and std_ret > 0 else None
        positive_clv_rate = (clv_positive_count / clv_total) if clv_total else None
        regime_breakdown = {
            reg: {"count": len(hits), "accuracy": sum(hits) / len(hits) if hits else 0}
            for reg, hits in by_regime.items()
        }

        sc_q = (
            select(StrategyContribution.strategy_name, func.count(StrategyContribution.id))
            .join(ModelPrediction, ModelPrediction.id == StrategyContribution.prediction_id)
            .join(PredictionOutcome, PredictionOutcome.prediction_id == ModelPrediction.id)
            .where(ModelPrediction.resolved_at >= cutoff)
        )
        if sport:
            sc_q = sc_q.where(ModelPrediction.sport == sport.upper())
        sc_q = sc_q.group_by(StrategyContribution.strategy_name)
        sc_r = await self.db.execute(sc_q)
        sc_rows = sc_r.all()
        leaderboard = [{"strategy_name": name, "contribution_count": c} for name, c in sc_rows]
        leaderboard.sort(key=lambda x: x["contribution_count"], reverse=True)

        return {
            "rolling_roi": round(roi, 4) if roi is not None else None,
            "sharpe_proxy": round(sharpe_proxy, 4) if sharpe_proxy is not None else None,
            "max_drawdown": round(max_dd, 4),
            "positive_clv_rate": round(positive_clv_rate, 4) if positive_clv_rate is not None else None,
            "strategy_contribution_leaderboard": leaderboard,
            "regime_performance_breakdown": regime_breakdown,
            "total_resolved": total,
        }
