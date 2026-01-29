"""Unit tests for NFL postseason week date ranges (weeks 19–22) with Super Bowl gap."""

from datetime import datetime, timedelta, timezone

import pytest

from app.utils.nfl_week import get_week_date_range


def test_postseason_week_22_start_is_14_days_after_week_21_start():
    """week22_start == week21_start + timedelta(days=14)."""
    week21_start, _ = get_week_date_range(21, 2025)
    week22_start, _ = get_week_date_range(22, 2025)
    assert week22_start == week21_start + timedelta(days=14)


def test_postseason_week_ranges_are_utc_tz_aware():
    """Both start datetimes are UTC tz-aware."""
    for week in (19, 20, 21, 22):
        start, end = get_week_date_range(week, 2025)
        assert start.tzinfo is not None
        assert end.tzinfo is not None
        assert start.tzinfo.utcoffset(start) == timedelta(0)
        assert end.tzinfo.utcoffset(end) == timedelta(0)


def test_postseason_weeks_19_20_21_are_seven_days_apart():
    """Weeks 19, 20, 21 each start 7 days after the previous."""
    w19_start, _ = get_week_date_range(19, 2025)
    w20_start, _ = get_week_date_range(20, 2025)
    w21_start, _ = get_week_date_range(21, 2025)
    assert w20_start == w19_start + timedelta(days=7)
    assert w21_start == w20_start + timedelta(days=7)
