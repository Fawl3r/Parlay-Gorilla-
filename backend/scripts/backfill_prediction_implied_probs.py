"""
One-time backfill: set implied_prob (implied_prob_market) for existing predictions
when odds are stored (implied_odds decimal). If no odds exist, skip safely.

Run manually: python -m scripts.backfill_prediction_implied_probs
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

# When run as script, ensure backend is on path (e.g. python scripts/backfill_prediction_implied_probs.py from backend)
_backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend not in sys.path:
    sys.path.insert(0, _backend)

from sqlalchemy import select, update
from app.database.session import AsyncSessionLocal
from app.models.model_prediction import ModelPrediction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ModelPrediction).where(
                ModelPrediction.implied_odds.isnot(None),
                ModelPrediction.implied_prob.is_(None),
            )
        )
        rows = result.scalars().all()
        if not rows:
            logger.info("No predictions with implied_odds and missing implied_prob; nothing to backfill.")
            return
        updated = 0
        for pred in rows:
            if pred.implied_odds and pred.implied_odds > 0:
                implied_prob = 1.0 / float(pred.implied_odds)
                if 0 < implied_prob <= 1:
                    pred.implied_prob = implied_prob
                    updated += 1
        await db.commit()
        logger.info("Backfill complete: updated implied_prob for %s predictions (of %s with odds).", updated, len(rows))


if __name__ == "__main__":
    asyncio.run(run())
