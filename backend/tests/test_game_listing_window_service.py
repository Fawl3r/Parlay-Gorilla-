"""Tests for game listing window by sport state and policy."""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.services.game_listing_window_service import (
    get_listing_window_for_sport_state,
    IN_SEASON_WINDOW_DAYS,
    PRESEASON_WINDOW_DAYS,
)
from app.services.sport_state_policy import CADENCE_DEFAULT_POLICY, EVENT_BASED_POLICY
from tests.ugie_fixtures import fixed_test_now


@pytest.fixture
def now():
    return fixed_test_now()


def test_offseason_returns_none(now):
    """OFFSEASON must return None so listing shows no far-future games."""
    window = get_listing_window_for_sport_state("OFFSEASON", now=now)
    assert window is None


def test_in_season_returns_window(now):
    """IN_SEASON returns window from now-past to now+in_season_days (cadence default)."""
    window = get_listing_window_for_sport_state("IN_SEASON", now=now)
    assert window is not None
    assert window.start_utc <= now
    assert window.end_utc >= now
    assert (window.end_utc - now).days == IN_SEASON_WINDOW_DAYS


def test_preseason_returns_window(now):
    """PRESEASON returns window up to preseason_days ahead (cadence default)."""
    window = get_listing_window_for_sport_state("PRESEASON", now=now)
    assert window is not None
    assert (window.end_utc - now).days == PRESEASON_WINDOW_DAYS


def test_in_break_returns_window(now):
    """IN_BREAK returns window up to preseason_days."""
    window = get_listing_window_for_sport_state("IN_BREAK", now=now)
    assert window is not None
    assert (window.end_utc - now).days == PRESEASON_WINDOW_DAYS


def test_postseason_returns_window(now):
    """POSTSEASON same as IN_SEASON for listing (cadence 10 days)."""
    window = get_listing_window_for_sport_state("POSTSEASON", now=now)
    assert window is not None
    assert (window.end_utc - now).days == IN_SEASON_WINDOW_DAYS


def test_cadence_policy_in_season_10_days(now):
    """Cadence policy: IN_SEASON uses listing_in_season_days=10."""
    window = get_listing_window_for_sport_state("IN_SEASON", now=now, policy=CADENCE_DEFAULT_POLICY)
    assert window is not None
    assert (window.end_utc - now).days == 10


def test_cadence_policy_preseason_60_days(now):
    """Cadence policy: PRESEASON uses listing_preseason_days=60."""
    window = get_listing_window_for_sport_state("PRESEASON", now=now, policy=CADENCE_DEFAULT_POLICY)
    assert window is not None
    assert (window.end_utc - now).days == 60


def test_event_based_policy_in_season_30_days(now):
    """Event-based policy: IN_SEASON uses listing_in_season_days=30."""
    window = get_listing_window_for_sport_state("IN_SEASON", now=now, policy=EVENT_BASED_POLICY)
    assert window is not None
    assert (window.end_utc - now).days == 30


def test_event_based_policy_preseason_90_days(now):
    """Event-based policy: PRESEASON uses listing_preseason_days=90."""
    window = get_listing_window_for_sport_state("PRESEASON", now=now, policy=EVENT_BASED_POLICY)
    assert window is not None
    assert (window.end_utc - now).days == 90


def test_offseason_returns_none_with_policy(now):
    """OFFSEASON returns None regardless of policy."""
    window = get_listing_window_for_sport_state("OFFSEASON", now=now, policy=EVENT_BASED_POLICY)
    assert window is None
