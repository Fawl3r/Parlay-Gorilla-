"""Tests for stats merge policy: primary (raw) overrides, fallback fills missing only."""

import pytest

from app.services.apisports.stats_merge import merge_stats


def test_merge_stats_primary_overrides() -> None:
    """Primary values are kept; fallback does not overwrite."""
    primary = {"points_for": 110, "wins": 42}
    fallback = {"points_for": 100, "losses": 30}
    out = merge_stats(primary, fallback)
    assert out["points_for"] == 110
    assert out["wins"] == 42
    assert out["losses"] == 30


def test_merge_stats_fallback_fills_missing_only() -> None:
    """Only keys missing in primary are added from fallback."""
    primary = {"fg_pct": 47.2}
    fallback = {"fg_pct": 50.0, "rebounds": 40.0}
    out = merge_stats(primary, fallback)
    assert out["fg_pct"] == 47.2
    assert out["rebounds"] == 40.0


def test_merge_stats_empty_primary_gets_all_fallback() -> None:
    out = merge_stats({}, {"wins": 10, "losses": 5})
    assert out == {"wins": 10, "losses": 5}


def test_merge_stats_fallback_none_values_not_filled() -> None:
    """None in fallback should not overwrite; we only fill missing keys."""
    primary = {}
    fallback = {"a": None, "b": 1}
    out = merge_stats(primary, fallback)
    assert "a" not in out or out.get("a") is None
    assert out.get("b") == 1
