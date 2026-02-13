"""
Sport state inference from DB games (no hardcoded dates).

Computes: OFFSEASON, PRESEASON, IN_SEASON, IN_BREAK, POSTSEASON from
windowed counts (in-season window, recent window, preseason window) and
next_game_at / last_game_at with sanity bounds. Uses per-sport policies.
POSTSEASON is set only when games have season_phase=postseason (metadata-based).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.services.sport_state_policy import SportStatePolicy, get_policy_for_sport

_FINISHED_STATUSES = ("finished", "closed", "complete", "Final", "final")


class SportState(str, Enum):
    OFFSEASON = "OFFSEASON"
    PRESEASON = "PRESEASON"
    IN_SEASON = "IN_SEASON"
    IN_BREAK = "IN_BREAK"
    POSTSEASON = "POSTSEASON"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def get_sport_state(
    db: AsyncSession,
    sport_code: str,
    now: Optional[datetime] = None,
    policy: Optional[SportStatePolicy] = None,
    offseason_days_since_last: int = 30,
) -> Dict[str, Any]:
    """
    Compute sport state from games table with per-sport policy and sanity logic.

    Returns dict with: sport_state, is_enabled, next_game_at, last_game_at,
    state_reason, upcoming_soon_count, recent_count, preseason_window_days,
    policy_mode, in_season_window_days, preseason_enable_days, etc.
    POSTSEASON is set only when upcoming games have season_phase="postseason".
    """
    now = now or _utc_now()
    policy = policy or get_policy_for_sport(sport_code)
    in_season_days = policy.in_season_window_days
    preseason_days = policy.preseason_window_days
    recent_days = policy.recent_window_days
    max_future = policy.max_future_sanity_days
    max_past = policy.max_past_sanity_days
    preseason_enable = policy.preseason_enable_days
    break_max_next = policy.break_max_next_days

    cutoff_recent = now - timedelta(days=recent_days)
    cutoff_in_season = now + timedelta(days=in_season_days)
    cutoff_future_sanity = now + timedelta(days=max_future)
    cutoff_past_sanity = now - timedelta(days=max_past)
    offseason_cutoff = now - timedelta(days=offseason_days_since_last)

    not_finished = (Game.status.is_(None)) | (Game.status.notin_(_FINISHED_STATUSES))

    # Upcoming soon (any): (now, now + in_season_window_days] → IN_SEASON signal
    upcoming_soon_result = await db.execute(
        select(func.count())
        .select_from(Game)
        .where(Game.sport == sport_code)
        .where(Game.start_time.is_not(None))
        .where(Game.start_time > now)
        .where(Game.start_time <= cutoff_in_season)
        .where(not_finished)
    )
    upcoming_soon_count = int(upcoming_soon_result.scalar_one() or 0)

    # Upcoming postseason soon: same window but season_phase == "postseason"
    upcoming_postseason_soon_result = await db.execute(
        select(func.count())
        .select_from(Game)
        .where(Game.sport == sport_code)
        .where(Game.start_time.is_not(None))
        .where(Game.start_time > now)
        .where(Game.start_time <= cutoff_in_season)
        .where(not_finished)
        .where(Game.season_phase == "postseason")
    )
    upcoming_postseason_soon_count = int(upcoming_postseason_soon_result.scalar_one() or 0)

    # Recent: [cutoff_recent, now]
    recent_result = await db.execute(
        select(func.count())
        .select_from(Game)
        .where(Game.sport == sport_code)
        .where(Game.start_time.is_not(None))
        .where(Game.start_time >= cutoff_recent)
        .where(Game.start_time <= now)
    )
    recent_count = int(recent_result.scalar_one() or 0)

    # Next game: earliest upcoming within sanity window
    next_result = await db.execute(
        select(func.min(Game.start_time))
        .select_from(Game)
        .where(Game.sport == sport_code)
        .where(Game.start_time.is_not(None))
        .where(Game.start_time > now)
        .where(Game.start_time <= cutoff_future_sanity)
        .where(not_finished)
    )
    next_game_at: Optional[datetime] = next_result.scalar_one_or_none()

    # Next postseason game (for stage_hint when state is POSTSEASON)
    next_postseason_result = await db.execute(
        select(Game)
        .where(Game.sport == sport_code)
        .where(Game.start_time.is_not(None))
        .where(Game.start_time > now)
        .where(Game.start_time <= cutoff_in_season)
        .where(not_finished)
        .where(Game.season_phase == "postseason")
        .order_by(Game.start_time)
        .limit(1)
    )
    next_postseason_game: Optional[Game] = next_postseason_result.scalars().first()

    # Last game: within past sanity window
    last_result = await db.execute(
        select(func.max(Game.start_time))
        .select_from(Game)
        .where(Game.sport == sport_code)
        .where(Game.start_time.is_not(None))
        .where(Game.start_time <= now)
        .where(Game.start_time >= cutoff_past_sanity)
    )
    last_game_at: Optional[datetime] = last_result.scalar_one_or_none()

    days_to_next: Optional[int] = None
    if next_game_at is not None:
        next_ = next_game_at
        now_ = now
        if next_.tzinfo is None and now.tzinfo is not None:
            next_ = next_.replace(tzinfo=now.tzinfo)
        if next_.tzinfo is not None and now.tzinfo is None:
            now_ = now.replace(tzinfo=next_.tzinfo)
        days_to_next = max(0, (next_ - now_).days)

    state: SportState
    reason: str
    is_enabled: bool
    season_phase_hint: Optional[str] = None
    stage_hint: Optional[str] = None

    if upcoming_postseason_soon_count > 0:
        state = SportState.POSTSEASON
        reason = "postseason_games_upcoming"
        is_enabled = True
        season_phase_hint = "postseason"
        if next_postseason_game and getattr(next_postseason_game, "stage", None):
            stage_hint = next_postseason_game.stage
    elif upcoming_soon_count > 0:
        state = SportState.IN_SEASON
        reason = "upcoming_within_in_season_window"
        is_enabled = True
    elif (
        recent_count > 0
        and (next_game_at is None or (days_to_next is not None and days_to_next > in_season_days))
        and days_to_next is not None
        and days_to_next <= break_max_next
    ):
        state = SportState.IN_BREAK
        reason = "recent_games_but_no_upcoming_soon"
        is_enabled = False
    elif next_game_at is not None and days_to_next is not None and days_to_next <= preseason_days:
        state = SportState.PRESEASON
        is_enabled = days_to_next <= preseason_enable
        reason = "preseason_approaching_enabled" if is_enabled else "preseason_not_yet_enabled"
    else:
        state = SportState.OFFSEASON
        is_enabled = False
        if last_game_at is None:
            reason = "no_games_in_db"
        else:
            last_utc = last_game_at if last_game_at.tzinfo else last_game_at.replace(tzinfo=timezone.utc)
            if last_utc < offseason_cutoff:
                reason = "last_game_beyond_offseason_threshold"
            else:
                reason = "no_games_soon"

    return {
        "sport_state": state.value,
        "is_enabled": is_enabled,
        "next_game_at": next_game_at.isoformat() if next_game_at else None,
        "last_game_at": last_game_at.isoformat() if last_game_at else None,
        "state_reason": reason,
        "upcoming_soon_count": upcoming_soon_count,
        "upcoming_postseason_soon_count": upcoming_postseason_soon_count,
        "recent_count": recent_count,
        "preseason_window_days": preseason_days,
        "preseason_enable_days": preseason_enable,
        "days_to_next": days_to_next,
        "policy_mode": policy.mode,
        "in_season_window_days": in_season_days,
        "recent_window_days": recent_days,
        "max_future_sanity_days": max_future,
        "season_phase_hint": season_phase_hint,
        "stage_hint": stage_hint,
    }
