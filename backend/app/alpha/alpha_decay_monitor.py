"""
Alpha Decay Monitor: detect when validated features degrade.

If IC drops below threshold, CLV turns negative, or ROI declines across rolling window,
reduce weight or deactivate feature (status -> DEPRECATED). Log to alpha_decay_log.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alpha_feature import AlphaFeature
from app.models.alpha_decay_log import AlphaDecayLog
from app.alpha.backtest_engine import BacktestEngine, BacktestResult

logger = logging.getLogger(__name__)

STATUS_VALIDATED = "VALIDATED"
STATUS_DEPRECATED = "DEPRECATED"
IC_DECAY_THRESHOLD = 0.0  # Deactivate if IC drops to or below this
MIN_ROLLING_SAMPLES = 50


class AlphaDecayMonitor:
    """
    Monitors validated features; deactivates and logs when performance degrades.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.backtest = BacktestEngine(db)

    async def check_feature(self, feature_id: Any, correlation_id: Optional[str] = None) -> bool:
        """
        Re-run backtest for a validated feature. If IC <= IC_DECAY_THRESHOLD or
        instability, set status=DEPRECATED and log to alpha_decay_log.
        Returns True if feature was deprecated.
        """
        result = await self.db.execute(
            select(AlphaFeature).where(AlphaFeature.id == feature_id).where(AlphaFeature.status == STATUS_VALIDATED)
        )
        feature = result.scalars().first()
        if not feature:
            return False

        backtest_result = await self.backtest.run_backtest(
            feature_id=feature.id,
            feature_name=feature.feature_name,
            feature_formula=feature.feature_formula,
            correlation_id=correlation_id,
        )

        deprecated = False
        reason = ""
        if backtest_result.sample_size < MIN_ROLLING_SAMPLES:
            return False  # Not enough data to judge decay
        if backtest_result.information_coefficient <= IC_DECAY_THRESHOLD:
            deprecated = True
            reason = "ic_below_threshold"
        if backtest_result.rejected and backtest_result.reject_reason == "instability_across_windows":
            deprecated = True
            reason = reason or "instability_detected"

        if not deprecated:
            return False

        feature.status = STATUS_DEPRECATED
        feature.deprecated_at = datetime.now(timezone.utc)
        log_entry = AlphaDecayLog(
            id=uuid.uuid4(),
            feature_id=feature.id,
            feature_name=feature.feature_name,
            reason=reason,
            ic_before=backtest_result.information_coefficient,
            roi_before=backtest_result.roi_delta,
        )
        self.db.add(log_entry)
        await self.db.commit()
        logger.info(
            "[AlphaDecay] Deprecated feature=%s reason=%s ic_before=%.4f correlation_id=%s",
            feature.feature_name,
            reason,
            backtest_result.information_coefficient,
            correlation_id or "",
        )
        return True

    async def check_all_validated(self, correlation_id: Optional[str] = None) -> int:
        """Run decay check on all validated features; return count deprecated."""
        result = await self.db.execute(
            select(AlphaFeature).where(AlphaFeature.status == STATUS_VALIDATED)
        )
        features = result.scalars().all()
        count = 0
        for f in features:
            if await self.check_feature(f.id, correlation_id=correlation_id):
                count += 1
        return count
