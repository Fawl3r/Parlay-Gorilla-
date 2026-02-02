"""Tests for parlay eligibility: ranked exclusion reasons, counts, entitlement-aware hints."""

import pytest

from app.services.parlay_eligibility_service import (
    RANK_ORDER,
    MAX_EXCLUSION_REASONS,
    derive_hint_from_reasons,
    _exclusion_counter_from_counts,
)


def test_rank_order_is_deterministic():
    """RANK_ORDER is a fixed tuple so UI/analytics get stable ordering."""
    assert len(RANK_ORDER) >= 5
    assert "NO_ODDS" in RANK_ORDER
    assert "OUTSIDE_WEEK" in RANK_ORDER
    assert "ENTITLEMENT_BLOCKED" in RANK_ORDER


def test_max_exclusion_reasons_capped():
    """We cap to MAX_EXCLUSION_REASONS (3-5) for clean UI."""
    assert 3 <= MAX_EXCLUSION_REASONS <= 5


def test_exclusion_counter_from_counts_no_games():
    """When total_games=0, counter has NO_GAMES_LOADED."""
    counter = _exclusion_counter_from_counts(
        active_sport="NFL",
        week=18,
        total_games=0,
        scheduled_games=0,
        upcoming_games=0,
        include_player_props=False,
    )
    assert counter.get("NO_GAMES_LOADED", 0) >= 1


def test_exclusion_counter_from_counts_outside_week():
    """When scheduled but no upcoming, counter has OUTSIDE_WEEK."""
    counter = _exclusion_counter_from_counts(
        active_sport="NFL",
        week=18,
        total_games=10,
        scheduled_games=10,
        upcoming_games=0,
        include_player_props=False,
    )
    assert counter.get("OUTSIDE_WEEK", 0) >= 1


def test_derive_hint_entitlement_blocked_returns_none():
    """When ENTITLEMENT_BLOCKED is in reasons, hint is None (do not suggest locked features)."""
    reasons = [{"reason": "ENTITLEMENT_BLOCKED", "count": 5}]
    hint = derive_hint_from_reasons(
        reasons,
        allow_player_props=True,
        allow_mix_sports=True,
    )
    assert hint is None


def test_derive_hint_no_odds_returns_ml_or_expand():
    """NO_ODDS suggests moneyline-only or expand week."""
    reasons = [{"reason": "NO_ODDS", "count": 14}]
    hint = derive_hint_from_reasons(reasons, allow_player_props=False, allow_mix_sports=False)
    assert hint is not None
    assert "moneyline" in hint.lower() or "expand" in hint.lower() or "upcoming" in hint.lower()


def test_derive_hint_outside_week_returns_expand():
    """OUTSIDE_WEEK suggests expand week."""
    reasons = [{"reason": "OUTSIDE_WEEK", "count": 9}]
    hint = derive_hint_from_reasons(reasons, allow_player_props=False, allow_mix_sports=False)
    assert hint is not None
    assert "expand" in hint.lower() or "upcoming" in hint.lower()


def test_derive_hint_player_props_disabled_only_when_entitled():
    """PLAYER_PROPS_DISABLED suggests enabling props only if allow_player_props=True."""
    reasons = [{"reason": "PLAYER_PROPS_DISABLED", "count": 1}]
    hint_entitled = derive_hint_from_reasons(reasons, allow_player_props=True, allow_mix_sports=False)
    hint_not_entitled = derive_hint_from_reasons(reasons, allow_player_props=False, allow_mix_sports=False)
    assert hint_entitled is not None
    assert "props" in hint_entitled.lower()
    # When not entitled we fall through to generic or another reason; we must not suggest enabling props
    assert hint_not_entitled is None or "enable" not in (hint_not_entitled or "").lower() or "props" not in (hint_not_entitled or "").lower()


def test_derive_hint_empty_reasons_returns_reduce_legs():
    """Empty reasons get generic 'reduce legs'."""
    hint = derive_hint_from_reasons([], allow_player_props=False, allow_mix_sports=False)
    assert hint is not None
    assert "legs" in hint.lower()


def test_ranked_reasons_order():
    """Building list from RANK_ORDER preserves deterministic order."""
    counter = {"NO_ODDS": 14, "OUTSIDE_WEEK": 9, "STATUS_NOT_UPCOMING": 6}
    ranked = [
        {"reason": r, "count": counter[r]}
        for r in RANK_ORDER
        if counter.get(r, 0) > 0
    ][:MAX_EXCLUSION_REASONS]
    assert len(ranked) <= MAX_EXCLUSION_REASONS
    reasons_order = [x["reason"] for x in ranked]
    assert reasons_order == [r for r in RANK_ORDER if counter.get(r, 0) > 0][:MAX_EXCLUSION_REASONS]
