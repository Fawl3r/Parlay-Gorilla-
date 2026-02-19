"""
Dataset-level telemetry for API-Sports enrichment (cache hit/miss, call_made, blocked, partial).
Uses composite metric names since telemetry.inc does not support labels.
"""

from __future__ import annotations

DATASETS = ("teams_index", "standings", "team_stats", "form", "injuries")


def _inc(metric: str, n: int = 1) -> None:
    try:
        from app.core import telemetry
        telemetry.inc(metric, n=n)
    except Exception:
        pass


def inc_cache_hit(dataset: str) -> None:
    _inc(f"apisports_cache_hit:{dataset}")


def inc_cache_miss(dataset: str) -> None:
    _inc(f"apisports_cache_miss:{dataset}")


def inc_call_made(dataset: str, sport: str = "") -> None:
    key = f"apisports_call_made:{dataset}"
    _inc(key)
    if sport:
        _inc(f"{key}:{sport}")


def inc_call_blocked_budget(dataset: str = "", sport: str = "") -> None:
    _inc("apisports_call_blocked_budget")
    if dataset:
        _inc(f"apisports_call_blocked_budget:{dataset}")
    if sport:
        _inc(f"apisports_call_blocked_budget:{sport}")


def inc_enrichment_partial(reason: str) -> None:
    _inc(f"enrichment_partial:{reason}")


def inc_enrichment_build_time_ms(ms: float) -> None:
    """Record enrichment build duration (counter; call once per build with ms)."""
    try:
        from app.core import telemetry
        telemetry.inc("enrichment_build_time_ms", n=max(0, int(ms)))
    except Exception:
        pass
