"""
Minimum viable end-to-end pipeline smoke script (not a test).

Proves the real pipeline works: create predictions -> resolve via PredictionTrackerService
-> get_model_health and get_accuracy_stats return expected shape.

Run from backend: python -m scripts.smoke_end_to_end_pipeline
Or: cd backend && python scripts/smoke_end_to_end_pipeline.py

Catches "works in unit tests but not in runtime hooks."
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import uuid

_backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend not in sys.path:
    sys.path.insert(0, _backend)

from app.database.session import AsyncSessionLocal
from app.services.prediction_tracker import PredictionTrackerService
from app.services.model_health_service import get_model_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fixed event_ids for reproducible smoke (no real Game rows required; resolver matches on game_id)
SMOKE_GAME_IDS = [
    "a0000001-0000-4000-8000-000000000001",
    "a0000001-0000-4000-8000-000000000002",
    "a0000001-0000-4000-8000-000000000003",
]


async def run() -> None:
    async with AsyncSessionLocal() as db:
        tracker = PredictionTrackerService(db)

        # 1) Create 2–3 predictions with known game_ids
        for i, game_id in enumerate(SMOKE_GAME_IDS):
            await tracker.save_prediction(
                game_id=game_id,
                sport="nfl",
                home_team="SmokeHome",
                away_team="SmokeAway",
                market_type="moneyline",
                team_side="home",
                predicted_prob=0.62,
                implied_prob=0.55,
                model_version="smoke-1.0",
            )
            logger.info("Created prediction for game_id=%s", game_id)

        # 2) Resolve them (WIN, LOSS, WIN) using the service
        outcomes_1 = await tracker.resolve_prediction(
            SMOKE_GAME_IDS[0],
            actual_winner_side="home",
            actual_score_home=24.0,
            actual_score_away=20.0,
        )
        outcomes_2 = await tracker.resolve_prediction(
            SMOKE_GAME_IDS[1],
            actual_winner_side="away",
            actual_score_home=10.0,
            actual_score_away=14.0,
        )
        outcomes_3 = await tracker.resolve_prediction(
            SMOKE_GAME_IDS[2],
            actual_winner_side="home",
            actual_score_home=31.0,
            actual_score_away=28.0,
        )
        logger.info("Resolved: %s, %s, %s outcomes", len(outcomes_1), len(outcomes_2), len(outcomes_3))

        # 3) Call get_model_health and get_accuracy_stats, print JSON
        health = await get_model_health(db)
        stats = await tracker.get_accuracy_stats(lookback_days=30)

        def _serialize(obj: object) -> object:
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            raise TypeError(type(obj))

        print("--- get_model_health ---")
        print(json.dumps(health, default=_serialize, indent=2))
        print("--- get_accuracy_stats ---")
        print(json.dumps(stats, default=_serialize, indent=2))

        # Sanity checks
        assert health["prediction_count_resolved"] >= 3, "expected at least 3 resolved"
        assert "pipeline_ok" in health and "pipeline_blockers" in health
        assert "resolved_predictions" in stats
        logger.info("Smoke OK: resolved=%s, pipeline_ok=%s", health["prediction_count_resolved"], health.get("pipeline_ok"))


if __name__ == "__main__":
    asyncio.run(run())
