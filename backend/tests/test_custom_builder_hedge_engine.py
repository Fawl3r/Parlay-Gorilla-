"""
Tests for Custom Builder hedge engine: flip_pick, counter ticket, coverage pack, upset possibilities.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest

from app.schemas.parlay import CustomParlayLeg
from app.services.custom_builder.hedge_engine import (
    build_coverage_pack,
    build_counter_ticket,
    build_upset_possibilities,
    flip_pick,
    is_supported_market,
    rank_picks_for_flipping,
)


@dataclass
class _FakeGame:
    id: uuid.UUID
    home_team: str
    away_team: str


def test_flip_pick_h2h():
    gid = uuid.uuid4()
    game = _FakeGame(id=gid, home_team="Bengals", away_team="Ravens")
    leg = CustomParlayLeg(game_id=str(gid), market_type="h2h", pick="Bengals")
    result = flip_pick(leg, game)
    assert result.game_id == str(gid)
    assert result.market_type == "h2h"
    assert result.selection == "away"
    assert result.line is None


def test_flip_pick_spread():
    gid = uuid.uuid4()
    game = _FakeGame(id=gid, home_team="Bengals", away_team="Ravens")
    leg = CustomParlayLeg(
        game_id=str(gid), market_type="spreads", pick="home", point=3.5
    )
    result = flip_pick(leg, game)
    assert result.game_id == str(gid)
    assert result.market_type == "spread"
    assert result.selection == "away"
    assert result.line == -3.5


def test_flip_pick_total():
    gid = uuid.uuid4()
    game = _FakeGame(id=gid, home_team="Bengals", away_team="Ravens")
    leg = CustomParlayLeg(
        game_id=str(gid), market_type="totals", pick="over", point=44.5
    )
    result = flip_pick(leg, game)
    assert result.game_id == str(gid)
    assert result.market_type == "total"
    assert result.selection == "under"
    assert result.line == 44.5


def test_flip_pick_moneyline_via_h2h():
    """Counter service expects 'h2h' for moneyline; hedge_engine normalizes output to h2h."""
    gid = uuid.uuid4()
    game = _FakeGame(id=gid, home_team="Lakers", away_team="Celtics")
    leg = CustomParlayLeg(game_id=str(gid), market_type="h2h", pick="away")
    result = flip_pick(leg, game)
    assert result.selection == "home"


def test_is_supported_market():
    leg_h2h = CustomParlayLeg(game_id="1", market_type="h2h", pick="home")
    leg_spread = CustomParlayLeg(game_id="1", market_type="spreads", pick="home")
    leg_total = CustomParlayLeg(game_id="1", market_type="totals", pick="over")
    leg_prop = CustomParlayLeg(game_id="1", market_type="player_points", pick="over")
    assert is_supported_market(leg_h2h) is True
    assert is_supported_market(leg_spread) is True
    assert is_supported_market(leg_total) is True
    assert is_supported_market(leg_prop) is False


def test_counter_ticket_returns_one_ticket_same_game_ids():
    g1 = uuid.uuid4()
    g2 = uuid.uuid4()
    games_by_id = {
        str(g1): _FakeGame(id=g1, home_team="A", away_team="B"),
        str(g2): _FakeGame(id=g2, home_team="C", away_team="D"),
    }
    legs = [
        CustomParlayLeg(game_id=str(g1), market_type="h2h", pick="A"),
        CustomParlayLeg(game_id=str(g2), market_type="h2h", pick="D"),
    ]
    ticket = build_counter_ticket(legs, games_by_id, mode="best_edges")
    assert ticket is not None
    assert ticket.flip_count >= 0
    assert len(ticket.picks) == 2
    game_ids = {p.game_id for p in ticket.picks}
    assert game_ids == {str(g1), str(g2)}


def test_counter_ticket_strict_flips_all():
    g1 = uuid.uuid4()
    games_by_id = {str(g1): _FakeGame(id=g1, home_team="A", away_team="B")}
    legs = [
        CustomParlayLeg(game_id=str(g1), market_type="h2h", pick="A"),
    ]
    ticket = build_counter_ticket(legs, games_by_id, mode="flip_all")
    assert ticket.flip_count == 1
    assert len(ticket.picks) == 1
    assert ticket.picks[0].selection == "away"


def test_coverage_pack_returns_at_most_20():
    games_by_id = {}
    legs = []
    for i in range(8):
        gid = uuid.uuid4()
        games_by_id[str(gid)] = _FakeGame(
            id=gid, home_team=f"Home{i}", away_team=f"Away{i}"
        )
        legs.append(
            CustomParlayLeg(
                game_id=str(gid), market_type="h2h", pick="home"
            )
        )
    pack = build_coverage_pack(legs, games_by_id, max_tickets=20)
    assert len(pack) <= 20
    assert len(pack) >= 1


def test_coverage_pack_unique_tickets():
    g1, g2, g3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    games_by_id = {
        str(g1): _FakeGame(id=g1, home_team="A", away_team="B"),
        str(g2): _FakeGame(id=g2, home_team="C", away_team="D"),
        str(g3): _FakeGame(id=g3, home_team="E", away_team="F"),
    }
    legs = [
        CustomParlayLeg(game_id=str(g1), market_type="h2h", pick="A"),
        CustomParlayLeg(game_id=str(g2), market_type="h2h", pick="C"),
        CustomParlayLeg(game_id=str(g3), market_type="h2h", pick="E"),
    ]
    pack = build_coverage_pack(legs, games_by_id, max_tickets=20)
    signatures = []
    for t in pack:
        sig = tuple(
            (p.game_id, p.market_type, p.selection, p.line)
            for p in sorted(t.picks, key=lambda x: (x.game_id, x.market_type))
        )
        signatures.append(sig)
    assert len(signatures) == len(set(signatures)), "coverage pack should have unique tickets"


def test_deterministic_order_stable():
    g1, g2 = uuid.uuid4(), uuid.uuid4()
    games_by_id = {
        str(g1): _FakeGame(id=g1, home_team="A", away_team="B"),
        str(g2): _FakeGame(id=g2, home_team="C", away_team="D"),
    }
    legs = [
        CustomParlayLeg(game_id=str(g1), market_type="h2h", pick="A"),
        CustomParlayLeg(game_id=str(g2), market_type="h2h", pick="C"),
    ]
    ticket1 = build_counter_ticket(legs, games_by_id, mode="best_edges")
    ticket2 = build_counter_ticket(legs, games_by_id, mode="best_edges")
    assert ticket1.flip_count == ticket2.flip_count
    assert len(ticket1.picks) == len(ticket2.picks)
    pack1 = build_coverage_pack(legs, games_by_id, max_tickets=10)
    pack2 = build_coverage_pack(legs, games_by_id, max_tickets=10)
    assert len(pack1) == len(pack2)


def test_build_upset_possibilities_n4():
    up = build_upset_possibilities(4)
    assert up.n == 4
    assert up.total == 16
    assert len(up.breakdown) == 5
    # C(4,0)=1, C(4,1)=4, C(4,2)=6, C(4,3)=4, C(4,4)=1
    assert up.breakdown[0].k == 0 and up.breakdown[0].count == 1
    assert up.breakdown[1].k == 1 and up.breakdown[1].count == 4
    assert up.breakdown[2].k == 2 and up.breakdown[2].count == 6
    assert up.breakdown[3].k == 3 and up.breakdown[3].count == 4
    assert up.breakdown[4].k == 4 and up.breakdown[4].count == 1


def test_rank_picks_for_flipping_lowest_confidence_first():
    g1 = uuid.uuid4()
    legs = [
        CustomParlayLeg(game_id=str(g1), market_type="h2h", pick="home"),
    ]
    # With signals: lower confidence first
    ranked = rank_picks_for_flipping(legs, pick_signals=[0.9])
    assert ranked == [0]
    ranked_multi = rank_picks_for_flipping(
        [
            CustomParlayLeg(game_id="a", market_type="totals", pick="over"),
            CustomParlayLeg(game_id="b", market_type="h2h", pick="home"),
        ],
        pick_signals=[0.3, 0.8],
    )
    # Lower confidence (0.3) should come first
    assert ranked_multi[0] == 0
    assert ranked_multi[1] == 1


def test_empty_legs():
    ticket = build_counter_ticket([], {}, mode="best_edges")
    assert ticket.flip_count == 0
    assert ticket.picks == []
    pack = build_coverage_pack([], {}, max_tickets=20)
    assert pack == []
    up = build_upset_possibilities(0)
    assert up.n == 0
    assert up.total == 1
    assert up.breakdown[0].k == 0 and up.breakdown[0].count == 1
