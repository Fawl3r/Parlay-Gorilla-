"""
Universal candidate window resolver: rolling truth + week fallback.
Lookback 12h; lookahead adjusted by season state (IN_SEASON 10d, POSTSEASON 14d, etc.).
NFL week mode returns week range; caller can fall back to rolling when 0 DB games.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from app.core.event_logger import log_event
from app.models.enums import SeasonState
from app.utils.nfl_week import get_week_date_range

logger = logging.getLogger(__name__)

LOOKBACK_HOURS = 12
LOOKAHEAD_DAYS_BY_STATE = {
    SeasonState.IN_SEASON: 10,
    SeasonState.POSTSEASON: 14,
    SeasonState.PRESEASON: 21,
    SeasonState.OFF_SEASON: 45,
}
DEFAULT_LOOKAHEAD_DAYS = 10


def resolve_candidate_window(
    sport: str,
    requested_week: Optional[int] = None,
    now_utc: Optional[datetime] = None,
    season_state: Optional[SeasonState] = None,
    trace_id: Optional[str] = None,
) -> Tuple[datetime, datetime, str]:
    """
    Resolve (start_utc, end_utc, mode) for candidate game window.

    - Rolling: lookback 12h, lookahead by season_state (default 10d).
    - NFL week: when requested_week is set, return get_week_date_range(week) with mode="week".
      Caller should fall back to rolling (mode="week_fallback_to_rolling") when 0 DB games.
    """
    now = now_utc or datetime.now(timezone.utc)
    sport_upper = (sport or "NFL").upper()

    if sport_upper == "NFL" and requested_week is not None:
        try:
            week_start, week_end = get_week_date_range(requested_week)
            log_event(
                logger,
                "parlay.generate.window_resolved",
                trace_id=trace_id,
                sport=sport_upper,
                mode="week",
                start_utc=week_start.isoformat(),
                end_utc=week_end.isoformat(),
                requested_week=requested_week,
                season_state=season_state.value if season_state else None,
            )
            return week_start, week_end, "week"
        except Exception as e:
            logger.warning("NFL week range failed for week=%s: %s; using rolling", requested_week, e)
            # Fall through to rolling

    lookahead_days = DEFAULT_LOOKAHEAD_DAYS
    if season_state is not None:
        lookahead_days = LOOKAHEAD_DAYS_BY_STATE.get(season_state, DEFAULT_LOOKAHEAD_DAYS)
    start_utc = now - timedelta(hours=LOOKBACK_HOURS)
    end_utc = now + timedelta(days=lookahead_days)
    mode = "rolling"
    log_event(
        logger,
        "parlay.generate.window_resolved",
        trace_id=trace_id,
        sport=sport_upper,
        mode=mode,
        start_utc=start_utc.isoformat(),
        end_utc=end_utc.isoformat(),
        season_state=season_state.value if season_state else None,
    )
    return start_utc, end_utc, mode
