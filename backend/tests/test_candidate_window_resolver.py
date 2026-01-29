"""Tests for CandidateWindowResolver and season-state-adjusted lookahead."""

from datetime import datetime, timedelta, timezone

import pytest

from app.models.enums import SeasonState
from app.services.probability_engine_impl.candidate_window_resolver import (
    resolve_candidate_window,
    LOOKBACK_HOURS,
    LOOKAHEAD_DAYS_BY_STATE,
)


def test_resolve_candidate_window_nfl_week_returns_week_mode():
    """NFL with requested_week returns week range and mode='week'."""
    start, end, mode = resolve_candidate_window("NFL", requested_week=1, now_utc=datetime(2025, 9, 10, 12, 0, tzinfo=timezone.utc))
    assert mode == "week"
    assert start.tzinfo is not None
    assert end.tzinfo is not None
    # Week 1 2025 starts around Sept 4
    assert start < end
    assert (end - start).days >= 6


def test_resolve_candidate_window_rolling_uses_lookback_and_lookahead():
    """Rolling window uses 12h lookback and season-state lookahead."""
    now = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
    start, end, mode = resolve_candidate_window("NFL", requested_week=None, now_utc=now, season_state=SeasonState.IN_SEASON)
    assert mode == "rolling"
    assert start == now - timedelta(hours=LOOKBACK_HOURS)
    assert end == now + timedelta(days=LOOKAHEAD_DAYS_BY_STATE[SeasonState.IN_SEASON])


def test_resolve_candidate_window_postseason_lookahead_14_days():
    """POSTSEASON uses 14d lookahead."""
    now = datetime(2025, 1, 20, 12, 0, tzinfo=timezone.utc)
    start, end, mode = resolve_candidate_window("NBA", now_utc=now, season_state=SeasonState.POSTSEASON)
    assert mode == "rolling"
    assert (end - now).days == 14

