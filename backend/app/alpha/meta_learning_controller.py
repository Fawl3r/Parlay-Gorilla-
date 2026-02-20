"""
Meta Learning Controller: decide when to retrain calibration, adjust strategy weights,
trigger experiments, and pause learning during unstable regimes.

Uses reinforcement feedback from institutional metrics (model_health_state, rolling ROI).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alpha_meta_state import AlphaMetaState
from app.models.model_health_state import ModelHealthState

logger = logging.getLogger(__name__)


class MetaLearningController:
    """
    Central controller for alpha learning: when to retrain, experiment, or pause.
    Reads model_health_state and alpha_meta_state; does not fabricate metrics.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_meta_state(self) -> AlphaMetaState:
        """Get or create singleton alpha_meta_state."""
        result = await self.db.execute(select(AlphaMetaState))
        row = result.scalars().first()
        if row:
            return row
        state = AlphaMetaState(learning_paused=False)
        self.db.add(state)
        await self.db.commit()
        await self.db.refresh(state)
        return state

    async def should_retrain_calibration(self) -> bool:
        """True if we should trigger calibration retrain (e.g. not paused, time since last)."""
        state = await self.get_meta_state()
        if state.learning_paused:
            return False
        # Could check last_retrain_at and interval (e.g. 7 days)
        return True

    async def should_run_experiment(self) -> bool:
        """True if we should launch an A/B experiment (not paused, regime stable)."""
        state = await self.get_meta_state()
        if state.learning_paused:
            return False
        return True

    async def should_pause_learning(self) -> bool:
        """True if regime is unstable (e.g. model_health_state RED)."""
        result = await self.db.execute(
            select(ModelHealthState).order_by(ModelHealthState.updated_at.desc()).limit(1)
        )
        health = result.scalars().first()
        if health and getattr(health, "model_state", None) == "RED":
            return True
        return False

    async def update_meta_state(
        self,
        learning_paused: Optional[bool] = None,
        regime: Optional[str] = None,
        last_retrain_at: Optional[bool] = None,
        last_experiment_at: Optional[bool] = None,
    ) -> None:
        """Update meta state (e.g. after retrain or experiment)."""
        state = await self.get_meta_state()
        if learning_paused is not None:
            state.learning_paused = learning_paused
        if regime is not None:
            state.regime = regime
        if last_retrain_at:
            state.last_retrain_at = datetime.now(timezone.utc)
        if last_experiment_at:
            state.last_experiment_at = datetime.now(timezone.utc)
        state.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        logger.debug("[MetaLearning] Updated meta state learning_paused=%s regime=%s", state.learning_paused, state.regime)
