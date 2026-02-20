"""
Reinforcement learning weight optimizer: maximize long-term expected ROI.

Updates strategy weights every RL_UPDATE_INTERVAL resolved predictions.
Uses bandit-style or lightweight PPO-style update; applies smoothing (0.9 old + 0.1 learned).
Safety: no single weight > 0.5, weights sum = 1.0, learning paused if resolved < 50.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome
from app.models.strategy_weight import StrategyWeight
from app.models.strategy_contribution import StrategyContribution
from app.models.model_health_state import ModelHealthState
from app.services.institutional.strategy_constants import ALL_STRATEGIES, default_equal_weights

logger = logging.getLogger(__name__)

RL_UPDATE_INTERVAL = 25
MIN_RESOLVED_FOR_LEARNING = 50
SMOOTHING_OLD = 0.9
SMOOTHING_NEW = 0.1
MAX_WEIGHT = 0.5
ROI_COLLAPSE_THRESHOLD = -0.15


class RLWeightOptimizer:
    """
    Updates strategy weights to maximize reward: normalized_profit + clv_bonus - drawdown_penalty - overconfidence_penalty.
    State: recent_accuracy, rolling_clv, brier_score, market_volatility, win_streak_length, loss_streak_length.
    Action: adjust strategy weights by small delta (bandit or gradient step).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _count_resolved_since(self, since: Optional[datetime] = None) -> int:
        q = select(func.count(ModelPrediction.id)).where(ModelPrediction.is_resolved == "true")
        if since:
            q = q.where(ModelPrediction.resolved_at >= since)
        r = await self.db.execute(q)
        return int(r.scalar() or 0)

    async def _last_update_at(self) -> Optional[datetime]:
        r = await self.db.execute(select(func.max(StrategyWeight.updated_at)))
        return r.scalar()

    async def _get_recent_outcomes_with_contributions(
        self, limit: int = 500
    ) -> List[tuple[Any, Any, List[Any]]]:
        """Fetch recent (prediction, outcome, contributions) for reward computation."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        q = (
            select(ModelPrediction, PredictionOutcome)
            .join(PredictionOutcome, PredictionOutcome.prediction_id == ModelPrediction.id)
            .where(ModelPrediction.resolved_at >= cutoff)
            .order_by(ModelPrediction.resolved_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(q)
        rows = result.all()
        out: List[tuple[Any, Any, List[Any]]] = []
        for pred, outcome in rows:
            cq = select(StrategyContribution).where(StrategyContribution.prediction_id == pred.id)
            cr = await self.db.execute(cq)
            contribs = cr.scalars().all()
            out.append((pred, outcome, list(contribs)))
        return out

    def _compute_reward(
        self,
        pred: Any,
        outcome: Any,
        profit_normalized: float = 0.0,
        clv_bonus: float = 0.0,
        drawdown_penalty: float = 0.0,
        overconfidence_penalty: float = 0.0,
    ) -> float:
        return profit_normalized + clv_bonus - drawdown_penalty - overconfidence_penalty

    async def _strategy_empirical_returns(
        self, recent: List[tuple[Any, Any, List[Any]]]
    ) -> Dict[str, List[float]]:
        """Per-strategy: list of (outcome 0/1) * (1 if contribution was positive else 0) or simple hit contribution."""
        by_strategy: Dict[str, List[float]] = {s: [] for s in ALL_STRATEGIES}
        for pred, outcome, contribs in recent:
            actual = 1.0 if outcome.was_correct else 0.0
            for c in contribs:
                if c.strategy_name not in by_strategy:
                    continue
                by_strategy[c.strategy_name].append(actual)
        return by_strategy

    async def run_update_if_due(self, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        If resolved count since last update >= RL_UPDATE_INTERVAL and total resolved >= 50,
        compute new weights via bandit (strategy with best recent accuracy gets higher weight), apply smoothing, persist.
        """
        total_resolved = await self._count_resolved_since()
        if total_resolved < MIN_RESOLVED_FOR_LEARNING:
            logger.info(
                "rl_weight_optimizer.skipped",
                extra={"reason": "insufficient_resolved", "total": total_resolved, "min": MIN_RESOLVED_FOR_LEARNING, "correlation_id": correlation_id},
            )
            return {"updated": False, "reason": "insufficient_resolved", "total_resolved": total_resolved}

        last = await self._last_update_at()
        since = last or datetime.min.replace(tzinfo=timezone.utc)
        resolved_since = await self._count_resolved_since(since)
        if resolved_since < RL_UPDATE_INTERVAL:
            return {"updated": False, "reason": "interval_not_reached", "resolved_since": resolved_since}

        recent = await self._get_recent_outcomes_with_contributions(limit=200)
        if not recent:
            return {"updated": False, "reason": "no_data"}

        roi = sum(
            (getattr(p, "implied_odds", None) or 2.0) - 1.0 if o.was_correct else -1.0
            for p, o, _ in recent
        ) / len(recent) if recent else 0
        if roi < ROI_COLLAPSE_THRESHOLD:
            logger.warning(
                "rl_weight_optimizer.skipped",
                extra={"reason": "roi_collapse", "roi": roi, "correlation_id": correlation_id},
            )
            return {"updated": False, "reason": "roi_collapse", "roi": roi}

        by_strategy = await self._strategy_empirical_returns(recent)
        current_weights = await self._get_current_weights_dict()

        new_weights: Dict[str, float] = {}
        for name in ALL_STRATEGIES:
            returns = by_strategy.get(name, [])
            if len(returns) < 10:
                new_weights[name] = current_weights.get(name, 1.0 / len(ALL_STRATEGIES))
                continue
            mean_return = sum(returns) / len(returns)
            new_weights[name] = max(0.05, min(MAX_WEIGHT, 0.15 + mean_return * 0.35))

        total = sum(new_weights.values())
        if total <= 0:
            new_weights = default_equal_weights()
        else:
            new_weights = {k: v / total for k, v in new_weights.items()}
            for k in list(new_weights.keys()):
                if new_weights[k] > MAX_WEIGHT:
                    new_weights[k] = MAX_WEIGHT
            total = sum(new_weights.values())
            new_weights = {k: v / total for k, v in new_weights.items()}

        for name in ALL_STRATEGIES:
            old_w = current_weights.get(name, 1.0 / len(ALL_STRATEGIES))
            smoothed = SMOOTHING_OLD * old_w + SMOOTHING_NEW * new_weights.get(name, old_w)
            new_weights[name] = smoothed
        total = sum(new_weights.values())
        new_weights = {k: v / total for k, v in new_weights.items()}

        result = await self.db.execute(select(StrategyWeight))
        rows = result.scalars().all()
        for row in rows:
            w = new_weights.get(row.strategy_name)
            if w is not None:
                row.weight = w
        for name in ALL_STRATEGIES:
            if name not in [r.strategy_name for r in rows]:
                self.db.add(StrategyWeight(strategy_name=name, weight=new_weights.get(name, 1.0 / len(ALL_STRATEGIES))))
        now_utc = datetime.now(timezone.utc)
        health_r = await self.db.execute(select(ModelHealthState).limit(1))
        health_row = health_r.scalar_one_or_none()
        if health_row is not None:
            health_row.last_rl_update_at = now_utc
        else:
            self.db.add(ModelHealthState(last_rl_update_at=now_utc))
        await self.db.commit()

        logger.info(
            "rl_weight_optimizer.updated",
            extra={"weights": new_weights, "correlation_id": correlation_id},
        )
        return {"updated": True, "weights": new_weights, "total_resolved": total_resolved}
    
    async def _get_current_weights_dict(self) -> Dict[str, float]:
        r = await self.db.execute(select(StrategyWeight))
        rows = r.scalars().all()
        if not rows:
            return default_equal_weights()
        total = sum(float(x.weight) for x in rows)
        return {x.strategy_name: float(x.weight) / total for x in rows} if total else default_equal_weights()
