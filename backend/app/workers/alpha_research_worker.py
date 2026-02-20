"""
Autonomous Alpha Research Worker: runs daily pipeline.

1. Generate candidate features (or rely on 12h feature discovery job)
2. Backtest candidates
3. Validate statistically
4. Launch experiments (when meta controller allows)
5. Promote winning alpha signals

All steps logged with correlation_id. No fabricated metrics.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from app.database.session import AsyncSessionLocal
from app.alpha.feature_discovery_engine import FeatureDiscoveryEngine
from app.alpha.backtest_engine import BacktestEngine
from app.alpha.alpha_validation_service import AlphaValidationService
from app.alpha.experimentation_engine import ExperimentationEngine
from app.alpha.strategy_graph_service import StrategyGraphService
from app.alpha.alpha_decay_monitor import AlphaDecayMonitor
from app.alpha.meta_learning_controller import MetaLearningController
from app.models.alpha_feature import AlphaFeature
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def run_alpha_research_cycle(correlation_id: str | None = None) -> dict:
    """
    One full cycle: generate candidates (if any new), backtest TESTING features,
    validate, run decay check on VALIDATED, optionally trigger experiments.
    Returns summary dict for telemetry.
    """
    cid = correlation_id or str(uuid.uuid4())
    summary = {
        "correlation_id": cid,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "candidates_created": 0,
        "validated": 0,
        "rejected": 0,
        "deprecated": 0,
        "experiments_started": 0,
        "errors": [],
    }
    try:
        async with AsyncSessionLocal() as db:
            # Optional: generate new candidates (feature_discovery runs every 12h separately)
            discovery = FeatureDiscoveryEngine(db)
            created = await discovery.generate_candidates(correlation_id=cid)
            summary["candidates_created"] = len(created)

            # Validate all TESTING features (backtest + gate)
            validation = AlphaValidationService(db)
            result = await db.execute(select(AlphaFeature).where(AlphaFeature.status == "TESTING"))
            testing = result.scalars().all()
            for f in testing:
                try:
                    promoted = await validation.validate_feature(str(f.id), correlation_id=cid)
                    if promoted:
                        summary["validated"] += 1
                    else:
                        summary["rejected"] += 1
                except Exception as e:
                    summary["errors"].append(f"validate:{f.feature_name}:{str(e)[:200]}")
                    logger.warning("[AlphaResearch] Validation failed for %s: %s", f.feature_name, e)

            # Decay check on VALIDATED
            decay = AlphaDecayMonitor(db)
            deprecated = await decay.check_all_validated(correlation_id=cid)
            summary["deprecated"] = deprecated

            # Optionally start experiments (meta controller)
            meta = MetaLearningController(db)
            if await meta.should_run_experiment():
                exp_engine = ExperimentationEngine(db)
                result = await db.execute(select(AlphaFeature).where(AlphaFeature.status == "VALIDATED"))
                validated_list = result.scalars().all()
                for f in validated_list[:1]:  # One experiment per cycle to limit load
                    try:
                        await exp_engine.start_experiment(
                            feature_id=f.id,
                            experiment_name=f"alpha_{f.feature_name}_{cid[:8]}",
                            correlation_id=cid,
                        )
                        summary["experiments_started"] += 1
                    except Exception as e:
                        summary["errors"].append(f"experiment:{f.feature_name}:{str(e)[:200]}")

        summary["finished_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(
            "[AlphaResearch] Cycle finished correlation_id=%s created=%s validated=%s rejected=%s deprecated=%s",
            cid,
            summary["candidates_created"],
            summary["validated"],
            summary["rejected"],
            summary["deprecated"],
        )
    except Exception as e:
        summary["errors"].append(str(e)[:500])
        logger.exception("[AlphaResearch] Cycle failed: %s", e)
    return summary


async def run_worker_loop(interval_hours: int = 24) -> None:
    """Run research cycle every interval_hours. For use by scheduler."""
    logger.info("[AlphaResearch] Worker started; interval=%s hours", interval_hours)
    while True:
        cid = str(uuid.uuid4())
        await run_alpha_research_cycle(correlation_id=cid)
        await asyncio.sleep(interval_hours * 3600)
