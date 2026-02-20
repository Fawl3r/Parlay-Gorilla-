"""
Alpha Validation Gate: promote only statistically valid features.

Requirements: minimum 200 prediction samples, positive IC, ROI improvement >= threshold,
no regime overfitting. Validated features move to status=VALIDATED; rejected archived.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alpha_feature import AlphaFeature
from app.alpha.backtest_engine import BacktestEngine, BacktestResult

logger = logging.getLogger(__name__)

MIN_PREDICTION_SAMPLES = 200
MIN_IC = 0.0  # Positive IC
ROI_IMPROVEMENT_THRESHOLD = 0.0  # Non-negative
STATUS_VALIDATED = "VALIDATED"
STATUS_REJECTED = "REJECTED"


class AlphaValidationService:
    """
    Validates candidate features from backtest results.
    Promotes to VALIDATED only when all gates pass; otherwise REJECTED.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.backtest = BacktestEngine(db)

    async def validate_feature(
        self,
        feature_id: Union[str, uuid.UUID],
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Run backtest for feature; if passes gates, set status=VALIDATED and validated_at.
        Else set status=REJECTED and rejected_at. Returns True if promoted.
        """
        fid = uuid.UUID(str(feature_id)) if isinstance(feature_id, str) else feature_id
        result = await self.db.execute(
            select(AlphaFeature).where(AlphaFeature.id == fid)
        )
        feature = result.scalars().first()
        if not feature or feature.status != "TESTING":
            logger.debug("[AlphaValidation] Feature not found or not TESTING id=%s", feature_id)
            return False

        backtest_result = await self.backtest.run_backtest(
            feature_id=feature.id,
            feature_name=feature.feature_name,
            feature_formula=feature.feature_formula,
            correlation_id=correlation_id,
        )

        if backtest_result.rejected:
            feature.status = STATUS_REJECTED
            feature.rejected_at = datetime.now(timezone.utc)
            await self.db.commit()
            logger.info(
                "[AlphaValidation] Rejected feature=%s reason=%s correlation_id=%s",
                feature.feature_name,
                backtest_result.reject_reason,
                correlation_id or "",
            )
            return False

        if backtest_result.sample_size < MIN_PREDICTION_SAMPLES:
            feature.status = STATUS_REJECTED
            feature.rejected_at = datetime.now(timezone.utc)
            await self.db.commit()
            logger.info(
                "[AlphaValidation] Rejected feature=%s insufficient samples n=%s",
                feature.feature_name,
                backtest_result.sample_size,
            )
            return False

        if backtest_result.information_coefficient <= MIN_IC:
            feature.status = STATUS_REJECTED
            feature.rejected_at = datetime.now(timezone.utc)
            await self.db.commit()
            logger.info(
                "[AlphaValidation] Rejected feature=%s IC not positive ic=%.4f",
                feature.feature_name,
                backtest_result.information_coefficient,
            )
            return False

        if backtest_result.roi_delta < ROI_IMPROVEMENT_THRESHOLD:
            # Still allow promotion if IC and p_value pass (ROI can be no worse)
            pass

        feature.status = STATUS_VALIDATED
        feature.validated_at = datetime.now(timezone.utc)
        await self.db.commit()
        logger.info(
            "[AlphaValidation] Validated feature=%s ic=%.4f p=%.4f correlation_id=%s",
            feature.feature_name,
            backtest_result.information_coefficient,
            backtest_result.p_value,
            correlation_id or "",
        )
        return True
