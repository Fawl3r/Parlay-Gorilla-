"""
Single source of truth for AI parlay eligibility.

Returns eligible leg count, unique games, and exclusion reasons for
preflight UI and structured 409 responses when generation fails.
"""

from __future__ import annotations

import logging
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.services.probability_engine import get_probability_engine

logger = logging.getLogger(__name__)

# Deterministic rank order for exclusion reasons (descending impact for UI/analytics).
RANK_ORDER = (
    "NO_ODDS",
    "OUTSIDE_WEEK",
    "STATUS_NOT_UPCOMING",
    "NO_GAMES_LOADED",
    "FEWER_UNIQUE_GAMES_THAN_LEGS",
    "PLAYER_PROPS_DISABLED",
    "ENTITLEMENT_BLOCKED",
    "UNKNOWN",
)
MAX_EXCLUSION_REASONS = 5


@dataclass(frozen=True)
class EligibilityResult:
    """Result of get_parlay_eligibility."""

    eligible_count: int  # candidate legs
    unique_games: int
    exclusion_reasons: List[Dict[str, Any]]  # [{"reason": str, "count": int}, ...] ranked, capped
    debug_id: str
    total_games: int = 0
    scheduled_games: int = 0
    upcoming_games: int = 0
    strong_edges: int = 0  # Candidates passing Triple strong-edge gate


def _count_strong_edges(candidates: List[dict], min_confidence: float = 0) -> int:
    """
    Count distinct games that have at least one candidate passing strong-edge gate
    (confidence >= TRIPLE_MIN_CONFIDENCE). This is the number of "slots" we can
    fill for a Triple (1 leg per game). confidence_score must be 0-100 (see triple_config).
    """
    from app.services.parlay_builder_impl.triple_config import TRIPLE_MIN_CONFIDENCE

    threshold = min_confidence if min_confidence > 0 else TRIPLE_MIN_CONFIDENCE
    games_with_strong = set()
    for c in (candidates or []):
        conf = float(c.get("confidence_score") or 0)
        assert 0 <= conf <= 100, "confidence_score must be 0-100 for Triple; got %s" % conf
        if conf < threshold:
            continue
        gid = c.get("game_id")
        if gid:
            games_with_strong.add(gid)
    return len(games_with_strong)


async def get_parlay_eligibility(
    db: AsyncSession,
    sport: str,
    num_legs: int,
    week: Optional[int] = None,
    include_player_props: bool = False,
    trace_id: Optional[str] = None,
    request_mode: Optional[str] = None,
) -> EligibilityResult:
    """
    Single eligibility source: run candidate pipeline once and optionally
    compute exclusion reasons when count is zero.

    When request_mode=TRIPLE, also computes strong_edges (candidates passing
    strong-edge gate for Triple confidence-gated selection).

    Returns eligible_count (candidate legs), unique_games, strong_edges (if TRIPLE), and top exclusion reasons.
    """
    debug_id = str(uuid.uuid4())[:8]
    active_sport = (sport or "NFL").upper()
    engine = get_probability_engine(db, active_sport)

    candidates = await engine.get_candidate_legs(
        sport=active_sport,
        min_confidence=0.0,
        max_legs=500,
        week=week,
        include_player_props=include_player_props,
        trace_id=trace_id,
    )

    eligible_count = len(candidates) if candidates else 0
    unique_games = len({c.get("game_id") for c in (candidates or []) if c.get("game_id")})
    strong_edges = 0
    if (request_mode or "").upper() == "TRIPLE" and candidates:
        strong_edges = _count_strong_edges(candidates, 0)  # uses TRIPLE_MIN_CONFIDENCE internally

    if eligible_count > 0:
        ranked: List[Dict[str, Any]] = []
        if unique_games < num_legs:
            ranked.append({"reason": "FEWER_UNIQUE_GAMES_THAN_LEGS", "count": max(0, num_legs - unique_games)})
        return EligibilityResult(
            eligible_count=eligible_count,
            unique_games=unique_games,
            exclusion_reasons=ranked[:MAX_EXCLUSION_REASONS],
            debug_id=debug_id,
            strong_edges=strong_edges,
        )

    # Build exclusion reasons from DB state (same logic as parlay_builder_service)
    scheduled_statuses = ("scheduled", "status_scheduled")
    total_result = await db.execute(select(func.count(Game.id)).where(Game.sport == active_sport))
    total_games = total_result.scalar() or 0

    scheduled_result = await db.execute(
        select(func.count(Game.id))
        .where(Game.sport == active_sport)
        .where(or_(Game.status.is_(None), func.lower(Game.status).in_(scheduled_statuses)))
    )
    scheduled_games = scheduled_result.scalar() or 0

    now = datetime.now(timezone.utc)
    future_cutoff = now + timedelta(days=14)
    upcoming_result = await db.execute(
        select(func.count(Game.id))
        .where(Game.sport == active_sport)
        .where(Game.start_time >= now)
        .where(Game.start_time <= future_cutoff)
        .where(or_(Game.status.is_(None), func.lower(Game.status).in_(scheduled_statuses)))
    )
    upcoming_games = upcoming_result.scalar() or 0

    counter = _exclusion_counter_from_counts(
        active_sport=active_sport,
        week=week,
        total_games=total_games,
        scheduled_games=scheduled_games,
        upcoming_games=upcoming_games,
        include_player_props=include_player_props,
    )
    ranked = [
        {"reason": r, "count": counter[r]}
        for r in RANK_ORDER
        if counter.get(r, 0) > 0
    ][:MAX_EXCLUSION_REASONS]

    return EligibilityResult(
        eligible_count=0,
        unique_games=0,
        exclusion_reasons=ranked,
        debug_id=debug_id,
        total_games=total_games,
        scheduled_games=scheduled_games,
        upcoming_games=upcoming_games,
        strong_edges=0,
    )


def _exclusion_counter_from_counts(
    active_sport: str,
    week: Optional[int],
    total_games: int,
    scheduled_games: int,
    upcoming_games: int,
    include_player_props: bool,
) -> Counter:
    """Build Counter of exclusion reason -> count (deterministic rank via RANK_ORDER)."""
    counter: Counter = Counter()
    if total_games == 0:
        counter["NO_GAMES_LOADED"] = 1
        return counter
    if scheduled_games == 0:
        counter["STATUS_NOT_UPCOMING"] = total_games
        return counter
    if upcoming_games == 0:
        counter["OUTSIDE_WEEK"] = scheduled_games
        return counter
    counter["NO_ODDS"] = upcoming_games
    if week is not None and active_sport == "NFL":
        counter["OUTSIDE_WEEK"] = counter.get("OUTSIDE_WEEK", 0) + 0  # hint: try all upcoming
    if include_player_props:
        counter["PLAYER_PROPS_DISABLED"] = 1
    return counter


def derive_hint_from_reasons(
    exclusion_reasons: List[Dict[str, Any]],
    allow_player_props: bool = False,
    allow_mix_sports: bool = False,
) -> Optional[str]:
    """
    Derive a single hint from ranked exclusion reasons. Never suggests locked features.
    """
    if not exclusion_reasons:
        return "Try reducing the number of legs."
    reasons_set = {r.get("reason") for r in exclusion_reasons if r.get("reason")}
    if "ENTITLEMENT_BLOCKED" in reasons_set:
        return None
    if "NO_ODDS" in reasons_set:
        return "Try moneyline-only picks or expand week to all upcoming games."
    if "OUTSIDE_WEEK" in reasons_set:
        return "Expand week to all upcoming games."
    if "STATUS_NOT_UPCOMING" in reasons_set:
        return "Try a different sport or week."
    if "NO_GAMES_LOADED" in reasons_set:
        return "Games may not have been loaded yet. Try again in a few moments."
    if "PLAYER_PROPS_DISABLED" in reasons_set and allow_player_props:
        return "Enable player props for more legs."
    if "FEWER_UNIQUE_GAMES_THAN_LEGS" in reasons_set:
        return "Try reducing legs or enable player props for more legs per game."
    return "Try reducing the number of legs."
