"""
Feature Discovery Engine: automatically generate candidate predictive features.

Generates features from: odds movement velocity, line reversal frequency,
bookmaker disagreement, time-to-start volatility, CLV momentum, prediction
confidence divergence, regime transition timing, historical matchup embeddings.
All features stored in alpha_features with status TESTING until validated.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alpha_feature import AlphaFeature

logger = logging.getLogger(__name__)

# Formula keys: each maps to a computation in backtest/valuation
FEATURE_TEMPLATES: List[Dict[str, str]] = [
    {"name": "odds_velocity_24h", "formula": "rate_of_change(implied_prob, 24h)"},
    {"name": "line_reversal_frequency_7d", "formula": "count_sign_flips(mid_odds, 7d)"},
    {"name": "bookmaker_disagreement_gradient", "formula": "std(books_implied_prob) / mean"},
    {"name": "time_to_start_volatility", "formula": "std(odds_snapshots) in 48h pre-start"},
    {"name": "clv_momentum_trend", "formula": "linear_slope(clv_series, 5_snapshots)"},
    {"name": "prediction_confidence_divergence", "formula": "|model_confidence - market_confidence|"},
    {"name": "regime_transition_timing", "formula": "days_since_regime_change(market_regime)"},
    {"name": "historical_matchup_embedding", "formula": "embedding(h2h_stats, team_form)"},
]

STATUS_TESTING = "TESTING"


class FeatureDiscoveryEngine:
    """
    Generates candidate alpha features and persists them to alpha_features.
    Does not fabricate performance; only creates feature definitions.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_candidates(self, correlation_id: Optional[str] = None) -> List[AlphaFeature]:
        """
        Generate candidate features from templates. Skips names that already exist.
        Returns list of newly created AlphaFeature records (status=TESTING).
        """
        created: List[AlphaFeature] = []
        existing = await self._existing_feature_names()
        for t in FEATURE_TEMPLATES:
            name = t["name"]
            formula = t.get("formula", "")
            if name in existing:
                logger.debug("[AlphaDiscovery] Skipping existing feature name=%s", name)
                continue
            try:
                feature = AlphaFeature(
                    id=uuid.uuid4(),
                    feature_name=name,
                    feature_formula=formula,
                    status=STATUS_TESTING,
                )
                self.db.add(feature)
                created.append(feature)
                logger.info(
                    "[AlphaDiscovery] Created candidate feature name=%s formula=%s correlation_id=%s",
                    name,
                    formula[:80] if formula else "",
                    correlation_id or "",
                )
            except Exception as e:
                logger.warning(
                    "[AlphaDiscovery] Failed to create feature name=%s: %s",
                    name,
                    e,
                    exc_info=True,
                )
        if created:
            await self.db.commit()
            for f in created:
                await self.db.refresh(f)
        return created

    async def _existing_feature_names(self) -> set:
        result = await self.db.execute(select(AlphaFeature.feature_name))
        rows = result.scalars().all() if result else []
        return {row[0] for row in rows} if rows else set()
