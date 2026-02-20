"""
Model Augmentation Pipeline: validated alpha features as additional inputs.

final_probability = base_model + calibration + institutional_weights + validated_alpha_contributions.
Alpha contribution weight capped initially at 5%; gradually increase via performance learning.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alpha_feature import AlphaFeature

logger = logging.getLogger(__name__)

ALPHA_WEIGHT_CAP_INITIAL = 0.05
STATUS_VALIDATED = "VALIDATED"
STATUS_DEPRECATED = "DEPRECATED"


class ModelAugmentationService:
    """
    Provides validated alpha feature list and their weight caps for the prediction pipeline.
    Does not modify UI or fabricate performance; only exposes which features to blend and cap.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_validated_alpha_contributions(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns list of {feature_name, weight_cap, feature_id} for validated (non-deprecated) features.
        context can contain prediction context (sport, matchup) for future per-context weights.
        """
        result = await self.db.execute(
            select(AlphaFeature)
            .where(AlphaFeature.status == STATUS_VALIDATED)
            .where(AlphaFeature.deprecated_at.is_(None))
        )
        features = result.scalars().all()
        out: List[Dict[str, Any]] = []
        for f in features:
            cap = f.weight_cap if f.weight_cap is not None else ALPHA_WEIGHT_CAP_INITIAL
            cap = min(cap, ALPHA_WEIGHT_CAP_INITIAL)  # Enforce initial cap
            out.append({
                "feature_id": str(f.id),
                "feature_name": f.feature_name,
                "weight_cap": cap,
            })
        return out

    async def compute_alpha_adjustment(
        self,
        base_prob: float,
        feature_values: Dict[str, float],
        correlation_id: Optional[str] = None,
    ) -> float:
        """
        Given base probability and a map of feature_name -> value (-1 to 1 scale),
        return adjustment to add to base (capped by ALPHA_WEIGHT_CAP_INITIAL total).
        feature_values must come from real data (caller responsibility).
        """
        contributions = await self.get_validated_alpha_contributions()
        if not contributions:
            return 0.0
        total_cap = ALPHA_WEIGHT_CAP_INITIAL
        per_feature = total_cap / len(contributions) if contributions else 0.0
        adjustment = 0.0
        for c in contributions:
            name = c["feature_name"]
            val = feature_values.get(name, 0.0)
            val = max(-1.0, min(1.0, float(val)))
            adjustment += per_feature * val
        adjustment = max(-total_cap, min(total_cap, adjustment))
        return adjustment
