"""
Result resolution worker: resolve model predictions when games finish.

Runs every 10 minutes. Fetches finished games via existing integrations,
matches event_id to unresolved predictions, sets resolved/result/resolved_at.
Idempotent; skips games older than 7 days. Retries and API failure protected.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, and_
from app.database.session import AsyncSessionLocal
from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome
from app.models.game import Game
from app.services.prediction_tracker import PredictionTrackerService, RESOLUTION_MAX_AGE_DAYS

logger = logging.getLogger(__name__)

_FINISHED_STATUSES = ("finished", "closed", "complete", "Final", "final", "FT", "FINAL")


async def run_result_resolution_cycle() -> int:
    """
    One cycle: find finished games with unresolved predictions, resolve them.
    Idempotent: already-resolved predictions are skipped.
    Returns number of predictions resolved.
    """
    resolved_count = 0
    resolution_mismatch_count = 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=RESOLUTION_MAX_AGE_DAYS)
    try:
        async with AsyncSessionLocal() as db:
            finished_games_result = await db.execute(
                select(Game)
                .where(Game.status.in_(_FINISHED_STATUSES))
                .where(Game.start_time >= cutoff)
            )
            finished_games = finished_games_result.scalars().all()

            tracker = PredictionTrackerService(db)
            for game in finished_games:
                home_score = getattr(game, "home_score", None)
                away_score = getattr(game, "away_score", None)
                if home_score is None or away_score is None:
                    resolution_mismatch_count += 1
                    logger.debug(
                        "resolution_mismatch",
                        extra={"event_id": str(game.id), "reason": "missing_scores"},
                    )
                    continue
                try:
                    actual_winner = "home" if home_score > away_score else "away"
                    if home_score == away_score:
                        actual_winner = "home"
                    outcomes = await tracker.resolve_prediction(
                        game_id=str(game.id),
                        actual_winner_side=actual_winner,
                        actual_score_home=float(home_score),
                        actual_score_away=float(away_score),
                    )
                    resolved_count += len(outcomes)
                except Exception as e:
                    logger.warning(
                        "[ResultResolutionWorker] Failed to resolve game %s: %s",
                        getattr(game, "id", None),
                        e,
                        exc_info=True,
                    )
                    resolution_mismatch_count += 1
            if resolved_count > 0 or resolution_mismatch_count > 0:
                logger.info(
                    "prediction_resolved",
                    extra={
                        "resolved_count": resolved_count,
                        "resolution_mismatch": resolution_mismatch_count,
                    },
                )
    except Exception as e:
        logger.exception("[ResultResolutionWorker] Cycle failed: %s", e)
    return resolved_count


async def run_worker_loop(interval_minutes: int = 10) -> None:
    """Run resolution cycle every interval_minutes. Idempotent per cycle."""
    logger.info("[ResultResolutionWorker] Started; interval=%s min", interval_minutes)
    while True:
        try:
            await run_result_resolution_cycle()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception("[ResultResolutionWorker] Loop error: %s", e)
        await asyncio.sleep(interval_minutes * 60)
