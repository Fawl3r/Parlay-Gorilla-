"""
Deterministic hedge engine: Counter Ticket (1) + Coverage Pack (<=20) + Upset Possibilities.

No analysis/API calls; reuses same games + markets. Flip logic only.
"""

from __future__ import annotations

import math
import uuid
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.custom_builder_hedge import (
    DerivedTicket,
    HedgePick,
    UpsetBreakdownItem,
    UpsetPossibilities,
)
from app.schemas.parlay import CustomParlayLeg
from app.services.custom_parlay.counter_service import CounterParlayService
from app.services.custom_parlay.odds_utils import OddsConverter

# Market type for HedgePick
_SUPPORTED = {"h2h", "moneyline", "spreads", "totals"}


def is_supported_market(leg: CustomParlayLeg) -> bool:
    """Only allow ML/h2h/spread/total."""
    mt = (leg.market_type or "").lower().strip()
    return mt in _SUPPORTED or mt in {"spread", "total"}  # singular


def _normalize_market_type(mt: str) -> str:
    if mt in ("h2h", "moneyline"):
        return "h2h"
    if mt in ("spreads", "spread"):
        return "spread"
    if mt in ("totals", "total"):
        return "total"
    return "h2h"


def _selection_from_leg(leg: CustomParlayLeg, home_team: str, away_team: str) -> str:
    """Normalize pick to home|away|over|under."""
    pick = (leg.pick or "").strip().lower()
    mt = (leg.market_type or "").lower().strip()
    if mt in ("totals", "total"):
        if pick == "over":
            return "over"
        if pick == "under":
            return "under"
        return "over"
    if pick in ("home", "away"):
        return pick
    if home_team and pick == home_team.lower():
        return "home"
    if away_team and pick == away_team.lower():
        return "away"
    return pick or "home"


def _leg_to_hedge_pick(leg: CustomParlayLeg, home_team: str, away_team: str) -> HedgePick:
    """Convert CustomParlayLeg to HedgePick (same side, normalized selection)."""
    mt = _normalize_market_type(leg.market_type or "h2h")
    selection = _selection_from_leg(leg, home_team, away_team)
    odds_dec: Optional[float] = None
    if leg.odds:
        try:
            odds_dec = OddsConverter.american_to_decimal(leg.odds)
        except Exception:
            pass
    return HedgePick(
        game_id=str(leg.game_id),
        market_type=mt,
        selection=selection,
        line=leg.point,
        odds=odds_dec,
    )


def flip_pick(leg: CustomParlayLeg, game: Any) -> HedgePick:
    """Flip leg to opposite side; return as HedgePick. Same games + markets."""
    flipped = CounterParlayService._flip_leg(game, leg)
    home = getattr(game, "home_team", "") or ""
    away = getattr(game, "away_team", "") or ""
    return _leg_to_hedge_pick(flipped, home, away)


def rank_picks_for_flipping(
    legs: List[CustomParlayLeg],
    pick_signals: Optional[List[float]] = None,
) -> List[int]:
    """
    Indices ordered for flipping: lowest confidence first (if signals),
    else totals > spreads > h2h; tie-break game_id + market_type.
    """
    n = len(legs)
    if n == 0:
        return []

    def key(i: int) -> Tuple[float, int, str, str]:
        # (ascending confidence, market_priority, game_id, market_type)
        conf = 1.0
        if pick_signals and i < len(pick_signals):
            conf = float(pick_signals[i])
            if conf > 1.0:
                conf = conf / 100.0
        mt = (legs[i].market_type or "h2h").lower().strip()
        if mt in ("totals", "total"):
            prio = 0
        elif mt in ("spreads", "spread"):
            prio = 1
        else:
            prio = 2
        gid = str(legs[i].game_id or "")
        return (conf, prio, gid, mt)

    indices = list(range(n))
    indices.sort(key=key)
    return indices


def build_counter_ticket(
    legs: List[CustomParlayLeg],
    games_by_id: Dict[str, Any],
    mode: str = "best_edges",
    pick_signals: Optional[List[float]] = None,
    target_flips: int = 2,
) -> DerivedTicket:
    """
    One counter ticket. Strict: flip all. Best edges: flip top target_flips (default 1-2).
    If no signals, label "Safer hedge" and flip by heuristic (totals/spreads first).
    """
    if not legs:
        return DerivedTicket(
            ticket_id=str(uuid.uuid4()),
            label="Counter Ticket",
            flip_count=0,
            picks=[],
            notes="No picks.",
        )
    ranked = rank_picks_for_flipping(legs, pick_signals)
    mode_lower = (mode or "best_edges").strip().lower()
    if mode_lower == "flip_all":
        flip_indices = set(range(len(legs)))
    else:
        x = min(target_flips, len(ranked), max(1, len(ranked) // 2 + 1))
        flip_indices = set(ranked[:x])

    picks: List[HedgePick] = []
    for i, leg in enumerate(legs):
        gid = str(uuid.UUID(str(leg.game_id)))
        game = games_by_id.get(gid)
        if not game:
            continue
        home = getattr(game, "home_team", "") or ""
        away = getattr(game, "away_team", "") or ""
        if i in flip_indices:
            picks.append(flip_pick(leg, game))
        else:
            picks.append(_leg_to_hedge_pick(leg, home, away))

    label = "Counter Ticket (Hedge)"
    notes = "This ticket hedges your riskiest picks."
    if mode_lower == "flip_all":
        notes = "Strict opposite of every pick."
    elif not pick_signals:
        notes = "Safer hedge — volatile markets flipped first."

    return DerivedTicket(
        ticket_id=str(uuid.uuid4()),
        label=label,
        flip_count=len(flip_indices),
        picks=picks,
        notes=notes,
    )


def _ticket_signature(picks: List[HedgePick]) -> Tuple[Tuple[str, str, str, Optional[float]], ...]:
    """Normalized signature for dedupe."""
    return tuple(
        (p.game_id, p.market_type, p.selection, p.line)
        for p in sorted(picks, key=lambda x: (x.game_id, x.market_type))
    )


def build_coverage_pack(
    legs: List[CustomParlayLeg],
    games_by_id: Dict[str, Any],
    pick_signals: Optional[List[float]] = None,
    max_tickets: int = 20,
    scenario_tickets: int = 10,
    round_robin_tickets: int = 10,
    round_robin_size: int = 2,
) -> List[DerivedTicket]:
    """
    Bounded set of hedge tickets. Scenario: k=1 and k=2 upsets first.
    Round-robin: subsets by dropping games, flip top 1 in each. Dedupe; cap max_tickets.
    """
    n = len(legs)
    if n == 0:
        return []
    ranked = rank_picks_for_flipping(legs, pick_signals)
    seen: set = set()
    out: List[DerivedTicket] = []

    def add_ticket(ticket: DerivedTicket) -> bool:
        sig = _ticket_signature(ticket.picks)
        if sig in seen or len(out) >= max_tickets:
            return False
        seen.add(sig)
        out.append(ticket)
        return True

    # k=1: flip each of top min(n, scenario_tickets) individually
    scenario_cap = min(n, scenario_tickets, max_tickets)
    for idx in ranked[:scenario_cap]:
        picks = []
        for i, leg in enumerate(legs):
            gid = str(uuid.UUID(str(leg.game_id)))
            game = games_by_id.get(gid)
            if not game:
                continue
            home = getattr(game, "home_team", "") or ""
            away = getattr(game, "away_team", "") or ""
            if i == idx:
                picks.append(flip_pick(leg, game))
            else:
                picks.append(_leg_to_hedge_pick(leg, home, away))
        if picks:
            add_ticket(
                DerivedTicket(
                    ticket_id=str(uuid.uuid4()),
                    label="1 upset hedge",
                    flip_count=1,
                    picks=picks,
                    notes="One pick flipped.",
                )
            )
        if len(out) >= max_tickets:
            return out

    # k=2: flip pairs from top M=min(6,n), deterministic order
    M = min(6, n)
    for i in range(M):
        for j in range(i + 1, M):
            if len(out) >= max_tickets:
                return out
            flip_set = {ranked[i], ranked[j]}
            picks = []
            for k, leg in enumerate(legs):
                gid = str(uuid.UUID(str(leg.game_id)))
                game = games_by_id.get(gid)
                if not game:
                    continue
                home = getattr(game, "home_team", "") or ""
                away = getattr(game, "away_team", "") or ""
                if k in flip_set:
                    picks.append(flip_pick(leg, game))
                else:
                    picks.append(_leg_to_hedge_pick(leg, home, away))
            if picks:
                add_ticket(
                    DerivedTicket(
                        ticket_id=str(uuid.uuid4()),
                        label="2 upset hedge",
                        flip_count=2,
                        picks=picks,
                        notes="Two picks flipped.",
                    )
                )

    # Round-robin style: drop round_robin_size games (cycle start index), flip top 1 in remaining
    drop_size = min(round_robin_size, n - 1)
    if drop_size >= 1 and round_robin_tickets > 0:
        for start in range(min(n, round_robin_tickets)):
            if len(out) >= max_tickets:
                return out
            keep = [(start + k) % n for k in range(n - drop_size)]
            flip_idx = next((r for r in ranked if r in keep), keep[0] if keep else ranked[0])
            picks = []
            for i in keep:
                leg = legs[i]
                gid = str(uuid.UUID(str(leg.game_id)))
                game = games_by_id.get(gid)
                if not game:
                    continue
                home = getattr(game, "home_team", "") or ""
                away = getattr(game, "away_team", "") or ""
                if i == flip_idx:
                    picks.append(flip_pick(leg, game))
                else:
                    picks.append(_leg_to_hedge_pick(leg, home, away))
            if picks:
                add_ticket(
                    DerivedTicket(
                        ticket_id=str(uuid.uuid4()),
                        label="Rotate games hedge",
                        flip_count=1,
                        picks=picks,
                        notes="Subset with one pick flipped.",
                    )
                )

    return out


def build_upset_possibilities(n: int) -> UpsetPossibilities:
    """Read-only: n picks, 2^n total, breakdown by k upsets (C(n,k))."""
    n = max(0, n)
    total = 1 << n if n <= 31 else 0
    breakdown = [
        UpsetBreakdownItem(k=k, count=math.comb(n, k) if n >= k else 0)
        for k in range(n + 1)
    ]
    return UpsetPossibilities(n=n, total=total, breakdown=breakdown)


class HedgeEngine:
    """Facade: build counter ticket, coverage pack, upset possibilities."""

    @staticmethod
    def run(
        legs: List[CustomParlayLeg],
        games_by_id: Dict[str, Any],
        mode: str = "best_edges",
        pick_signals: Optional[List[float]] = None,
        max_coverage_tickets: int = 20,
        scenario_tickets: int = 10,
        round_robin_tickets: int = 10,
        round_robin_size: int = 2,
    ) -> Tuple[DerivedTicket, List[DerivedTicket], UpsetPossibilities]:
        counter = build_counter_ticket(legs, games_by_id, mode, pick_signals)
        coverage = build_coverage_pack(
            legs,
            games_by_id,
            pick_signals,
            max_tickets=max_coverage_tickets,
            scenario_tickets=scenario_tickets,
            round_robin_tickets=round_robin_tickets,
            round_robin_size=round_robin_size,
        )
        upset = build_upset_possibilities(len(legs))
        return counter, coverage, upset
