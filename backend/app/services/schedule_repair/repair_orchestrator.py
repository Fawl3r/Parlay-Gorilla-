"""
Schedule repair orchestrator: DB-detect placeholder games in window;
run APISports repair first (if critical and quota allows), then ESPN fallback.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_logger import log_event
from app.models.enums import SeasonState
from app.models.game import Game
from app.services.apisports.quota_manager import get_quota_manager
from app.services.schedule_repair.apisports_repair import ApiSportsRepairPass
from app.services.schedule_repair.espn_repair import EspnRepairPass
from app.services.season_state_service import SeasonStateService
from app.utils.placeholders import is_placeholder_team

logger = logging.getLogger(__name__)


class ScheduleRepairOrchestrator:
    """
    Repair placeholder team names in a time window.
    Critical when season_state == POSTSEASON or a placeholder game is in the next 72h.
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._apisports = ApiSportsRepairPass(db)
        self._espn = EspnRepairPass(db)
        self._quota = get_quota_manager()
        self._season_state = SeasonStateService(db)

    async def repair_placeholders(
        self,
        sport: str,
        window_start: datetime,
        window_end: datetime,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Detect placeholder games in [window_start, window_end]; run APISports then ESPN repair.
        Returns {found, fixed, providers_used}.
        """
        sport_upper = (sport or "NFL").upper()
        log_event(
            logger,
            "schedule.repair.start",
            trace_id=trace_id,
            sport=sport_upper,
            window_start=window_start.isoformat(),
            window_end=window_end.isoformat(),
        )
        result = await self._db.execute(
            select(Game)
            .where(Game.sport == sport_upper)
            .where(Game.start_time >= window_start)
            .where(Game.start_time <= window_end)
            .where(
                or_(
                    Game.home_team.in_(["TBD", "TBA", "AFC", "NFC"]),
                    Game.away_team.in_(["TBD", "TBA", "AFC", "NFC"]),
                )
            )
        )
        candidates = result.scalars().all()
        placeholder_games = [g for g in candidates if is_placeholder_team(g.home_team) or is_placeholder_team(g.away_team)]
        found = len(placeholder_games)
        if not placeholder_games:
            log_event(
                logger,
                "schedule.repair.done",
                trace_id=trace_id,
                sport=sport_upper,
                found=0,
                fixed=0,
                providers_used=[],
            )
            return {"found": 0, "fixed": 0, "providers_used": []}

        now = datetime.now(timezone.utc)
        season_state = await self._season_state.get_season_state(sport_upper, now_utc=now)
        critical = (
            season_state == SeasonState.POSTSEASON
            or any(
                g.start_time and (g.start_time - now).total_seconds() <= 72 * 3600
                for g in placeholder_games
            )
        )
        fixed = 0
        providers_used: List[str] = []

        try:
            if critical:
                decision = await self._quota.check_quota(sport_upper, 1, critical=True)
                if not decision.allowed:
                    try:
                        from app.services.alerting import get_alerting_service
                        await get_alerting_service().emit(
                            "provider.quota.state",
                            "warning",
                            {
                                "allowed": False,
                                "reason": decision.reason,
                                "used": decision.used,
                                "limit": decision.limit,
                                "context": "schedule_repair_critical",
                            },
                            sport=sport_upper,
                        )
                    except Exception as alert_err:
                        logger.debug("Alerting emit skipped: %s", alert_err)
                elif decision.allowed:
                    fixed_apisports = await self._apisports.repair(sport_upper, placeholder_games, trace_id=trace_id)
                    if fixed_apisports > 0:
                        fixed += fixed_apisports
                        providers_used.append("apisports")
                        log_event(
                            logger,
                            "schedule.repair.applied",
                            trace_id=trace_id,
                            sport=sport_upper,
                            provider="apisports",
                            fixed=fixed_apisports,
                        )
                    placeholder_games = [g for g in placeholder_games if is_placeholder_team(g.home_team) or is_placeholder_team(g.away_team)]

            if placeholder_games:
                log_event(
                    logger,
                    "schedule.repair.fallback_to_espn",
                    trace_id=trace_id,
                    sport=sport_upper,
                    remaining=len(placeholder_games),
                )
                fixed_espn = await self._espn.repair(sport_upper, placeholder_games, trace_id=trace_id)
                if fixed_espn > 0:
                    fixed += fixed_espn
                    if "espn" not in providers_used:
                        providers_used.append("espn")

            if fixed > 0:
                try:
                    await self._db.commit()
                except Exception as e:
                    logger.warning("Schedule repair commit failed: %s", e)
                    await self._db.rollback()
                    try:
                        from app.services.alerting import get_alerting_service
                        await get_alerting_service().emit(
                            "schedule.repair.fail",
                            "error",
                            {"reason": "commit_failed", "message": str(e)[:200]},
                            sport=sport_upper,
                        )
                    except Exception as alert_err:
                        logger.debug("Alerting emit skipped: %s", alert_err)
        except Exception as repair_err:
            logger.warning("Schedule repair failed: %s", repair_err)
            try:
                from app.services.alerting import get_alerting_service
                await get_alerting_service().emit(
                    "schedule.repair.fail",
                    "error",
                    {"reason": "repair_exception", "message": str(repair_err)[:200]},
                    sport=sport_upper,
                )
            except Exception as alert_err:
                logger.debug("Alerting emit skipped: %s", alert_err)
            raise

        log_event(
            logger,
            "schedule.repair.done",
            trace_id=trace_id,
            sport=sport_upper,
            found=found,
            fixed=fixed,
            providers_used=providers_used,
        )
        return {"found": found, "fixed": fixed, "providers_used": providers_used}
