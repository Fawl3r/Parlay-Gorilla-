"""Tests for offseason fallback return dates."""

from datetime import datetime, timezone

import pytest

from app.services.offseason_return_dates import get_offseason_fallback_return_date


def test_ncaaf_returns_august_date():
    """NCAAF fallback is late August."""
    # Feb 2026 -> next opener Aug 29, 2026
    now = datetime(2026, 2, 13, 12, 0, 0, tzinfo=timezone.utc)
    out = get_offseason_fallback_return_date("NCAAF", now)
    assert out is not None
    assert out.month == 8
    assert out.day == 29
    assert out.year == 2026


def test_nfl_returns_september_date():
    """NFL fallback is early September."""
    now = datetime(2026, 2, 13, 12, 0, 0, tzinfo=timezone.utc)
    out = get_offseason_fallback_return_date("NFL", now)
    assert out is not None
    assert out.month == 9
    assert out.year == 2026


def test_ufc_no_fallback():
    """UFC has no configured opener."""
    now = datetime(2026, 2, 13, 12, 0, 0, tzinfo=timezone.utc)
    assert get_offseason_fallback_return_date("UFC", now) is None


def test_empty_sport_code_returns_none():
    assert get_offseason_fallback_return_date("", None) is None
    assert get_offseason_fallback_return_date("  ", None) is None


def test_past_opener_uses_next_year():
    """When 'now' is after this year's opener, return next year's opener."""
    # Dec 2026 -> NCAAF next is Aug 29, 2027
    now = datetime(2026, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
    out = get_offseason_fallback_return_date("NCAAF", now)
    assert out is not None
    assert out.year == 2027
    assert out.month == 8
    assert out.day == 29
