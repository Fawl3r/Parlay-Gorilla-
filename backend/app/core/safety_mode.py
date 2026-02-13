"""
Safety Mode: GREEN / YELLOW / RED for parlay generation.

- GREEN: normal.
- YELLOW: degraded (cap legs, attach warning).
- RED: generation frozen (return safe response).

Anti-flap: RED/YELLOW cooldowns hold state for a minimum duration.
Deterministic and testable; reads from app.core.telemetry and app.core.config.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

from app.core import telemetry as telemetry_module
from app.core.config import settings

_LAST_EFFECTIVE_KEY = "_last_effective_state"


def _compute_raw_state(snap: Dict[str, Any], now_ts: float) -> Tuple[str, List[str]]:
    """Compute state from metrics only (no cooldown). Returns (state, reasons)."""
    reasons: List[str] = []
    err_5m = snap.get("error_count_5m", 0)
    red_err = getattr(settings, "safety_mode_red_error_count_5m", 25)
    if err_5m >= red_err:
        reasons.append(f"error_count_5m={err_5m} >= {red_err}")
    neg_30m = snap.get("not_enough_games_failures_30m", 0)
    red_neg = getattr(settings, "safety_mode_red_not_enough_games_30m", 10)
    if neg_30m >= red_neg:
        reasons.append(f"not_enough_games_failures_30m={neg_30m} >= {red_neg}")
    if reasons:
        return "RED", reasons

    reasons = []
    stale_odds = getattr(settings, "safety_mode_stale_odds_seconds", 900)
    stale_games = getattr(settings, "safety_mode_stale_games_seconds", 3600)
    last_odds = snap.get("last_successful_odds_refresh_at")
    last_games = snap.get("last_successful_games_refresh_at")
    try:
        if last_odds is not None and (now_ts - float(last_odds)) > stale_odds:
            reasons.append("odds_data_stale")
        if last_games is not None and (now_ts - float(last_games)) > stale_games:
            reasons.append("games_data_stale")
    except (TypeError, ValueError):
        if last_odds is None:
            reasons.append("odds_refresh_unknown")
        if last_games is None:
            reasons.append("games_refresh_unknown")
    try:
        budget_ratio = float(getattr(settings, "safety_mode_yellow_api_budget_ratio", 0.80) or 0.80)
    except (TypeError, ValueError):
        budget_ratio = 0.80
    used = snap.get("estimated_api_calls_today", 0) or 0
    try:
        used = int(used) if used is not None else 0
    except (TypeError, ValueError):
        used = 0
    budget = snap.get("daily_api_budget") or getattr(settings, "apisports_daily_quota", 100)
    try:
        budget = int(budget) if budget is not None else 100
    except (TypeError, ValueError):
        budget = 100
    if budget > 0 and used >= budget * budget_ratio:
        reasons.append(f"api_budget_ratio={used}/{budget} >= {budget_ratio}")
    gen_fail_5m = snap.get("generation_failures_5m", 0)
    try:
        yellow_gen = int(getattr(settings, "safety_mode_yellow_gen_failures_5m", 10) or 10)
    except (TypeError, ValueError):
        yellow_gen = 10
    if gen_fail_5m >= yellow_gen:
        reasons.append(f"generation_failures_5m={gen_fail_5m} >= {yellow_gen}")
    api_fail_30m = snap.get("api_failures_30m", 0)
    yellow_api = getattr(settings, "safety_mode_yellow_api_failures_30m", 15)
    if api_fail_30m >= yellow_api:
        reasons.append(f"api_failures_30m={api_fail_30m} >= {yellow_api}")
    if reasons:
        return "YELLOW", reasons
    return "GREEN", []


class SafetyModeBlocked(Exception):
    """Raised when generation is blocked (RED). Payload for API response."""

    def __init__(self, state: str, message: str, reasons: List[str], snapshot: Dict[str, Any]):
        self.state = state
        self.message = message
        self.reasons = reasons
        self.snapshot = snapshot
        super().__init__(message)


def get_safety_state() -> str:
    """Return GREEN, YELLOW, or RED (with anti-flap cooldown)."""
    if not getattr(settings, "safety_mode_enabled", True):
        return "GREEN"

    now_ts = time.time()
    snap = telemetry_module.get_snapshot()
    raw_state, raw_reasons = _compute_raw_state(snap, now_ts)

    red_min = int(getattr(settings, "safety_mode_red_min_seconds", 300) or 300)
    yellow_min = int(getattr(settings, "safety_mode_yellow_min_seconds", 60) or 60)

    if raw_state == "RED":
        telemetry_module.set("safety_red_since", now_ts)
    else:
        red_since = snap.get("safety_red_since")
        if red_since is not None:
            try:
                if (now_ts - float(red_since)) >= red_min:
                    telemetry_module.set("safety_red_since", None)
            except (TypeError, ValueError):
                pass

    if raw_state == "YELLOW":
        telemetry_module.set("safety_yellow_since", now_ts)
    elif raw_state == "GREEN":
        yellow_since = snap.get("safety_yellow_since")
        if yellow_since is not None:
            try:
                if (now_ts - float(yellow_since)) >= yellow_min:
                    telemetry_module.set("safety_yellow_since", None)
            except (TypeError, ValueError):
                pass

    # Re-read after possibly updating cooldown timestamps
    snap = telemetry_module.get_snapshot()
    red_since = snap.get("safety_red_since")
    yellow_since = snap.get("safety_yellow_since")

    effective = raw_state
    if red_since is not None:
        try:
            if (now_ts - float(red_since)) < red_min:
                effective = "RED"
        except (TypeError, ValueError):
            pass
    if effective == "GREEN" and yellow_since is not None:
        try:
            if (now_ts - float(yellow_since)) < yellow_min:
                effective = "YELLOW"
        except (TypeError, ValueError):
            pass

    last = telemetry_module.get(_LAST_EFFECTIVE_KEY)
    if last != effective:
        telemetry_module.record_safety_event(last or "GREEN", effective, raw_reasons if effective != "GREEN" else [])
        telemetry_module.set(_LAST_EFFECTIVE_KEY, effective)

    return effective


def get_safety_snapshot() -> Dict[str, Any]:
    """Full snapshot: state, reasons, telemetry (no secrets)."""
    snap = telemetry_module.get_snapshot()
    state = get_safety_state()
    reasons: List[str] = []

    if state == "RED":
        err_5m = snap.get("error_count_5m", 0)
        red_err = getattr(settings, "safety_mode_red_error_count_5m", 25)
        if err_5m >= red_err:
            reasons.append(f"error_count_5m={err_5m} >= {red_err}")
        neg_30m = snap.get("not_enough_games_failures_30m", 0)
        red_neg = getattr(settings, "safety_mode_red_not_enough_games_30m", 10)
        if neg_30m >= red_neg:
            reasons.append(f"not_enough_games_failures_30m={neg_30m} >= {red_neg}")
    else:
        stale_odds = getattr(settings, "safety_mode_stale_odds_seconds", 900)
        stale_games = getattr(settings, "safety_mode_stale_games_seconds", 3600)
        last_odds = snap.get("last_successful_odds_refresh_at")
        last_games = snap.get("last_successful_games_refresh_at")
        now = __import__("time").time()
        if last_odds is not None:
            try:
                if (now - float(last_odds)) > stale_odds:
                    reasons.append("odds_data_stale")
            except (TypeError, ValueError):
                pass
        if last_games is not None:
            try:
                if (now - float(last_games)) > stale_games:
                    reasons.append("games_data_stale")
            except (TypeError, ValueError):
                pass
        budget_ratio = getattr(settings, "safety_mode_yellow_api_budget_ratio", 0.80)
        used = snap.get("estimated_api_calls_today", 0) or 0
        budget = snap.get("daily_api_budget") or getattr(settings, "apisports_daily_quota", 100)
        if budget > 0 and used >= budget * budget_ratio:
            reasons.append(f"api_budget_ratio >= {budget_ratio}")
        if snap.get("generation_failures_5m", 0) >= getattr(settings, "safety_mode_yellow_gen_failures_5m", 10):
            reasons.append("generation_failures_5m")
        if snap.get("api_failures_30m", 0) >= getattr(settings, "safety_mode_yellow_api_failures_30m", 15):
            reasons.append("api_failures_30m")

    snap_with_budget = dict(snap)
    snap_with_budget["daily_api_budget"] = getattr(settings, "apisports_daily_quota", 100)
    return {
        "state": state,
        "reasons": reasons,
        "telemetry": snap_with_budget,
        "safety_mode_enabled": getattr(settings, "safety_mode_enabled", True),
        "events": telemetry_module.get_safety_events(),
    }


def require_generation_allowed() -> None:
    """
    If RED, raise SafetyModeBlocked with message and reasons.
    Call at start of parlay generation handler.
    """
    state = get_safety_state()
    if state == "RED":
        snap = get_safety_snapshot()
        raise SafetyModeBlocked(
            state=state,
            message="Parlay generation temporarily paused for data reliability. Try again soon.",
            reasons=snap["reasons"],
            snapshot=snap,
        )


def apply_degraded_policy(request_params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    In YELLOW, cap num_legs to SAFETY_MODE_YELLOW_MAX_LEGS.
    Returns (adjusted_params, policies_applied).
    """
    state = get_safety_state()
    out = dict(request_params) if request_params else {}
    policies: List[str] = []
    if state != "YELLOW":
        return out, policies
    max_legs = getattr(settings, "safety_mode_yellow_max_legs", 4)
    if "num_legs" in out and (out["num_legs"] or 0) > max_legs:
        out["num_legs"] = max_legs
        policies.append("cap_legs")
    return out, policies
