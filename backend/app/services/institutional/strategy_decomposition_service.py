"""
Strategy decomposition layer: compute final probability as weighted ensemble of strategy signals.

Each prediction stores strategy_components (all signals 0-1) and strategy_contributions (per-strategy).
Final probability = sum(weight_i * strategy_output_i). Weights from strategy_weights table or equal default.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.strategy_weight import StrategyWeight
from app.services.institutional.strategy_constants import (
    ALL_STRATEGIES,
    default_equal_weights,
    STRATEGY_BASE_MODEL,
    STRATEGY_CALIBRATION,
    STRATEGY_CLV,
    STRATEGY_HISTORICAL_ACCURACY,
    STRATEGY_MARKET_DISAGREEMENT,
    STRATEGY_VOLATILITY,
)

logger = logging.getLogger(__name__)


def _clamp_prob(p: float) -> float:
    return max(0.01, min(0.99, float(p)))


class StrategyDecompositionService:
    """Computes ensemble probability from strategy signals; loads weights from DB."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_default_weights(self) -> None:
        """Seed strategy_weights with equal weights if table is empty. Idempotent."""
        result = await self.db.execute(select(StrategyWeight).limit(1))
        if result.scalar_one_or_none() is not None:
            return
        for name in ALL_STRATEGIES:
            w = StrategyWeight(strategy_name=name, weight=1.0 / len(ALL_STRATEGIES))
            self.db.add(w)
        await self.db.commit()
        logger.info("institutional.strategy_weights.seeded", extra={"strategies": len(ALL_STRATEGIES)})

    async def get_weights(self) -> Dict[str, float]:
        """Load strategy weights from DB; normalize to sum 1.0; cap each at 0.5."""
        result = await self.db.execute(select(StrategyWeight))
        rows = result.scalars().all()
        if not rows:
            await self.ensure_default_weights()
            result = await self.db.execute(select(StrategyWeight))
            rows = result.scalars().all()
        if not rows:
            return default_equal_weights()
        weights = {r.strategy_name: float(r.weight) for r in rows if r.strategy_name in ALL_STRATEGIES}
        for s in ALL_STRATEGIES:
            if s not in weights:
                weights[s] = 1.0 / len(ALL_STRATEGIES)
        total = sum(weights.values())
        if total <= 0:
            return default_equal_weights()
        weights = {k: v / total for k, v in weights.items()}
        for k in list(weights.keys()):
            if weights[k] > 0.5:
                weights[k] = 0.5
        total = sum(weights.values())
        if total <= 0:
            return default_equal_weights()
        return {k: v / total for k, v in weights.items()}

    async def compute_ensemble(
        self,
        implied_prob: float,
        model_adjusted_prob: float,
        sport: str,
        home_team: str,
        away_team: str,
        calibration_delta: float = 0.0,
        rolling_accuracy: Optional[float] = None,
        volatility_signal: Optional[float] = None,
        clv_signal: Optional[float] = None,
    ) -> Tuple[float, Dict[str, float], List[Tuple[str, float, float]]]:
        """
        Compute final probability as weighted sum of strategy signals.

        Returns:
            (final_prob, strategy_components dict, list of (strategy_name, weight, contribution_value))
        """
        implied = _clamp_prob(implied_prob)
        model = _clamp_prob(model_adjusted_prob)

        calibration_prob = _clamp_prob(implied + calibration_delta)
        clv = _clamp_prob(clv_signal) if clv_signal is not None else implied
        acc = _clamp_prob(rolling_accuracy) if rolling_accuracy is not None else 0.5
        vol = _clamp_prob(volatility_signal) if volatility_signal is not None else 0.5
        disagreement = model

        components = {
            STRATEGY_BASE_MODEL: implied,
            STRATEGY_CALIBRATION: calibration_prob,
            STRATEGY_CLV: clv,
            STRATEGY_MARKET_DISAGREEMENT: disagreement,
            STRATEGY_HISTORICAL_ACCURACY: acc,
            STRATEGY_VOLATILITY: vol,
        }

        weights = await self.get_weights()
        contributions: List[Tuple[str, float, float]] = []
        final = 0.0
        for name in ALL_STRATEGIES:
            w = weights.get(name, 1.0 / len(ALL_STRATEGIES))
            val = components.get(name, 0.5)
            contrib = w * val
            contributions.append((name, w, contrib))
            final += contrib

        final = _clamp_prob(final)
        return final, components, contributions
