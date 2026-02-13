"""Tests for Safety Mode: state decision, RED block, YELLOW cap, cooldown, events."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from app.core import telemetry as telemetry_module
from app.core.safety_mode import (
    SafetyModeBlocked,
    apply_degraded_policy,
    get_safety_state,
    get_safety_snapshot,
    require_generation_allowed,
)


@pytest.mark.unit
def test_safety_state_green_when_healthy():
    """With no bad telemetry and fresh timestamps, state is GREEN."""
    now = time.time()
    healthy_snap = {
        "error_count_5m": 0,
        "not_enough_games_failures_30m": 0,
        "last_successful_odds_refresh_at": now,
        "last_successful_games_refresh_at": now,
        "estimated_api_calls_today": 10,
        "generation_failures_5m": 0,
        "api_failures_30m": 0,
    }
    with patch("app.core.safety_mode.telemetry_module.get_snapshot", return_value=healthy_snap):
        with patch("app.core.safety_mode.settings") as mock_settings:
            mock_settings.safety_mode_enabled = True
            mock_settings.safety_mode_red_error_count_5m = 25
            mock_settings.safety_mode_red_not_enough_games_30m = 10
            mock_settings.safety_mode_stale_odds_seconds = 900
            mock_settings.safety_mode_stale_games_seconds = 3600
            mock_settings.safety_mode_yellow_api_budget_ratio = 0.80
            mock_settings.safety_mode_yellow_gen_failures_5m = 10
            mock_settings.safety_mode_yellow_api_failures_30m = 15
            mock_settings.apisports_daily_quota = 100
            state = get_safety_state()
    assert state == "GREEN"


@pytest.mark.unit
def test_safety_state_red_when_error_count_exceeded():
    """When error_count_5m >= threshold, state is RED."""
    red_snap = {"error_count_5m": 25, "not_enough_games_failures_30m": 0}
    with patch("app.core.safety_mode.telemetry_module.get_snapshot", return_value=red_snap):
        with patch("app.core.safety_mode.settings") as mock_settings:
            mock_settings.safety_mode_enabled = True
            mock_settings.safety_mode_red_error_count_5m = 25
            mock_settings.safety_mode_red_not_enough_games_30m = 10
            state = get_safety_state()
    assert state == "RED"


@pytest.mark.unit
def test_safety_state_yellow_when_stale():
    """When last refresh is older than stale threshold, state is YELLOW."""
    old = time.time() - 2000
    yellow_snap = {
        "error_count_5m": 0,
        "not_enough_games_failures_30m": 0,
        "last_successful_odds_refresh_at": old,
        "last_successful_games_refresh_at": old,
        "estimated_api_calls_today": 10,
        "generation_failures_5m": 0,
        "api_failures_30m": 0,
    }
    with patch("app.core.safety_mode.telemetry_module.get_snapshot", return_value=yellow_snap):
        with patch("app.core.safety_mode.settings") as mock_settings:
            mock_settings.safety_mode_enabled = True
            mock_settings.safety_mode_red_error_count_5m = 25
            mock_settings.safety_mode_red_not_enough_games_30m = 10
            mock_settings.safety_mode_stale_odds_seconds = 900
            mock_settings.safety_mode_stale_games_seconds = 3600
            mock_settings.safety_mode_yellow_api_budget_ratio = 0.80
            mock_settings.safety_mode_yellow_gen_failures_5m = 10
            mock_settings.safety_mode_yellow_api_failures_30m = 15
            mock_settings.apisports_daily_quota = 100
            state = get_safety_state()
    assert state == "YELLOW"


@pytest.mark.unit
def test_require_generation_allowed_raises_when_red():
    """require_generation_allowed raises SafetyModeBlocked when state is RED."""
    red_snap = {"error_count_5m": 25, "not_enough_games_failures_30m": 0}
    with patch("app.core.safety_mode.telemetry_module.get_snapshot", return_value=red_snap):
        with patch("app.core.safety_mode.settings") as mock_settings:
            mock_settings.safety_mode_enabled = True
            mock_settings.safety_mode_red_error_count_5m = 25
            mock_settings.safety_mode_red_not_enough_games_30m = 10
            with pytest.raises(SafetyModeBlocked) as exc_info:
                require_generation_allowed()
            assert exc_info.value.state == "RED"
            assert "reasons" in exc_info.value.snapshot


@pytest.mark.unit
def test_apply_degraded_policy_caps_legs_when_yellow():
    """In YELLOW, apply_degraded_policy caps num_legs to max."""
    yellow_snap = {
        "error_count_5m": 0,
        "not_enough_games_failures_30m": 0,
        "last_successful_odds_refresh_at": time.time() - 2000,
        "last_successful_games_refresh_at": time.time() - 2000,
        "estimated_api_calls_today": 10,
        "generation_failures_5m": 0,
        "api_failures_30m": 0,
    }
    with patch("app.core.safety_mode.telemetry_module.get_snapshot", return_value=yellow_snap):
        with patch("app.core.safety_mode.settings") as mock_settings:
            mock_settings.safety_mode_enabled = True
            mock_settings.safety_mode_red_error_count_5m = 25
            mock_settings.safety_mode_red_not_enough_games_30m = 10
            mock_settings.safety_mode_stale_odds_seconds = 900
            mock_settings.safety_mode_stale_games_seconds = 3600
            mock_settings.safety_mode_yellow_api_budget_ratio = 0.80
            mock_settings.safety_mode_yellow_gen_failures_5m = 10
            mock_settings.safety_mode_yellow_api_failures_30m = 15
            mock_settings.safety_mode_yellow_max_legs = 4
            mock_settings.apisports_daily_quota = 100
            state = get_safety_state()
            assert state == "YELLOW"
            out, policies = apply_degraded_policy({"num_legs": 6, "risk_profile": "balanced"})
            assert out["num_legs"] == 4
            assert "cap_legs" in policies
            out2, policies2 = apply_degraded_policy({"num_legs": 3})
            assert out2["num_legs"] == 3
            assert policies2 == []


@pytest.mark.unit
def test_get_safety_snapshot_structure():
    """get_safety_snapshot returns state, reasons, telemetry, safety_mode_enabled, events."""
    snap = get_safety_snapshot()
    assert "state" in snap
    assert snap["state"] in ("GREEN", "YELLOW", "RED")
    assert "reasons" in snap
    assert isinstance(snap["reasons"], list)
    assert "telemetry" in snap
    assert "safety_mode_enabled" in snap
    assert "events" in snap
    assert isinstance(snap["events"], list)


@pytest.mark.unit
def test_red_cooldown_holds_until_expiry():
    """When state was RED, it stays RED until safety_mode_red_min_seconds elapses."""
    now = time.time()
    red_snap = {"error_count_5m": 25, "not_enough_games_failures_30m": 0}
    healthy_snap = {
        "error_count_5m": 0,
        "not_enough_games_failures_30m": 0,
        "last_successful_odds_refresh_at": now,
        "last_successful_games_refresh_at": now,
        "estimated_api_calls_today": 10,
        "generation_failures_5m": 0,
        "api_failures_30m": 0,
    }
    call_count = [0]

    def snap_side_effect():
        call_count[0] += 1
        if call_count[0] == 1:
            return dict(red_snap)
        return {**healthy_snap, "safety_red_since": now - 10}

    with patch("app.core.safety_mode.telemetry_module.get_snapshot", side_effect=snap_side_effect):
        with patch("app.core.safety_mode.telemetry_module.get", return_value=None):
            with patch("app.core.safety_mode.telemetry_module.set"):
                with patch("app.core.safety_mode.telemetry_module.record_safety_event"):
                    with patch("app.core.safety_mode.settings") as mock_settings:
                        mock_settings.safety_mode_enabled = True
                        mock_settings.safety_mode_red_error_count_5m = 25
                        mock_settings.safety_mode_red_not_enough_games_30m = 10
                        mock_settings.safety_mode_red_min_seconds = 300
                        mock_settings.safety_mode_yellow_min_seconds = 60
                        mock_settings.safety_mode_stale_odds_seconds = 900
                        mock_settings.safety_mode_stale_games_seconds = 3600
                        mock_settings.safety_mode_yellow_api_budget_ratio = 0.80
                        mock_settings.safety_mode_yellow_gen_failures_5m = 10
                        mock_settings.safety_mode_yellow_api_failures_30m = 15
                        mock_settings.apisports_daily_quota = 100
                        state1 = get_safety_state()
                        state2 = get_safety_state()
    assert state1 == "RED"
    assert state2 == "RED"


@pytest.mark.unit
def test_ring_buffer_records_transitions():
    """GREEN -> YELLOW -> RED produces events with correct from_state/to_state."""
    telemetry_module.set("_last_effective_state", None)
    try:
        with patch("app.core.safety_mode.telemetry_module.get_snapshot") as mock_snap:
            with patch("app.core.safety_mode.telemetry_module.get", side_effect=[None, "GREEN", "YELLOW"]):
                with patch("app.core.safety_mode.telemetry_module.set"):
                    with patch("app.core.safety_mode.settings") as mock_settings:
                        mock_settings.safety_mode_enabled = True
                        mock_settings.safety_mode_red_error_count_5m = 25
                        mock_settings.safety_mode_red_not_enough_games_30m = 10
                        mock_settings.safety_mode_red_min_seconds = 300
                        mock_settings.safety_mode_yellow_min_seconds = 60
                        mock_settings.safety_mode_stale_odds_seconds = 900
                        mock_settings.safety_mode_stale_games_seconds = 3600
                        mock_settings.safety_mode_yellow_api_budget_ratio = 0.80
                        mock_settings.safety_mode_yellow_gen_failures_5m = 10
                        mock_settings.safety_mode_yellow_api_failures_30m = 15
                        mock_settings.apisports_daily_quota = 100
                        now = time.time()
                        mock_snap.return_value = {
                            "error_count_5m": 0,
                            "not_enough_games_failures_30m": 0,
                            "last_successful_odds_refresh_at": now - 2000,
                            "last_successful_games_refresh_at": now - 2000,
                            "estimated_api_calls_today": 10,
                            "generation_failures_5m": 0,
                            "api_failures_30m": 0,
                        }
                        get_safety_state()
                        get_safety_state()
        events = telemetry_module.get_safety_events()
        assert isinstance(events, list)
    finally:
        telemetry_module.set("_last_effective_state", None)


@pytest.mark.unit
def test_apply_degraded_policy_returns_policies_applied():
    """apply_degraded_policy returns (adjusted_params, policies); cap_legs when num_legs > max."""
    stub_snapshot = {"state": "YELLOW", "reasons": [], "telemetry": {}, "events": []}
    with patch("app.core.safety_mode.get_safety_state", return_value="YELLOW"):
        with patch("app.core.safety_mode.get_safety_snapshot", return_value=stub_snapshot):
            with patch("app.core.safety_mode.settings") as mock_settings:
                mock_settings.safety_mode_yellow_max_legs = 4
                out, policies = apply_degraded_policy({"num_legs": 10, "risk_profile": "balanced"})
                assert out["num_legs"] == 4
                assert policies == ["cap_legs"]
    with patch("app.core.safety_mode.get_safety_state", return_value="GREEN"):
        out2, policies2 = apply_degraded_policy({"num_legs": 10, "risk_profile": "balanced"})
        assert out2["num_legs"] == 10
        assert policies2 == []


# --- v1.2: model drift, ROI proxy, correlation ---


@pytest.mark.unit
def test_confidence_drift_triggers_yellow():
    """When high_conf_loss_rate_24h > threshold, state is YELLOW with confidence_calibration_drift."""
    now = time.time()
    snap = {
        "error_count_5m": 0,
        "not_enough_games_failures_30m": 0,
        "last_successful_odds_refresh_at": now,
        "last_successful_games_refresh_at": now,
        "estimated_api_calls_today": 10,
        "generation_failures_5m": 0,
        "api_failures_30m": 0,
        "high_conf_loss_rate_24h": 0.60,
    }
    with patch("app.core.safety_mode.telemetry_module.get_snapshot", return_value=snap):
        with patch("app.core.safety_mode.settings") as mock_settings:
            mock_settings.safety_mode_enabled = True
            mock_settings.safety_mode_red_error_count_5m = 25
            mock_settings.safety_mode_red_not_enough_games_30m = 10
            mock_settings.safety_mode_stale_odds_seconds = 900
            mock_settings.safety_mode_stale_games_seconds = 3600
            mock_settings.safety_mode_yellow_api_budget_ratio = 0.80
            mock_settings.safety_mode_yellow_gen_failures_5m = 10
            mock_settings.safety_mode_yellow_api_failures_30m = 15
            mock_settings.safety_mode_high_conf_max_loss_rate = 0.55
            mock_settings.safety_mode_performance_delta = 0.05
            mock_settings.safety_mode_drift_red_hours = 48
            mock_settings.safety_mode_correlation_legs_threshold = 5
            mock_settings.apisports_daily_quota = 100
            state = get_safety_state()
            assert state == "YELLOW"
            full = get_safety_snapshot()
            assert full["state"] == "YELLOW"
            assert "confidence_calibration_drift" in full["reasons"] or full["telemetry"].get("high_conf_loss_rate_24h") == 0.60


@pytest.mark.unit
def test_sustained_drift_triggers_red_after_cooldown():
    """When YELLOW for confidence_calibration_drift persists > drift_red_hours, state becomes RED."""
    now = time.time()
    # Simulate we have been YELLOW for 49 hours
    yellow_since = now - (49 * 3600)
    snap = {
        "error_count_5m": 0,
        "not_enough_games_failures_30m": 0,
        "last_successful_odds_refresh_at": now,
        "last_successful_games_refresh_at": now,
        "estimated_api_calls_today": 10,
        "generation_failures_5m": 0,
        "api_failures_30m": 0,
        "high_conf_loss_rate_24h": 0.60,
        "safety_yellow_since": yellow_since,
    }
    with patch("app.core.safety_mode.telemetry_module.get_snapshot", return_value=snap):
        with patch("app.core.safety_mode.telemetry_module.get", return_value=None):
            with patch("app.core.safety_mode.telemetry_module.set"):
                with patch("app.core.safety_mode.telemetry_module.record_safety_event"):
                    with patch("app.core.safety_mode.settings") as mock_settings:
                        mock_settings.safety_mode_enabled = True
                        mock_settings.safety_mode_red_error_count_5m = 25
                        mock_settings.safety_mode_red_not_enough_games_30m = 10
                        mock_settings.safety_mode_stale_odds_seconds = 900
                        mock_settings.safety_mode_stale_games_seconds = 3600
                        mock_settings.safety_mode_yellow_api_budget_ratio = 0.80
                        mock_settings.safety_mode_yellow_gen_failures_5m = 10
                        mock_settings.safety_mode_yellow_api_failures_30m = 15
                        mock_settings.safety_mode_high_conf_max_loss_rate = 0.55
                        mock_settings.safety_mode_performance_delta = 0.05
                        mock_settings.safety_mode_drift_red_hours = 48
                        mock_settings.safety_mode_correlation_legs_threshold = 5
                        mock_settings.apisports_daily_quota = 100
                        state = get_safety_state()
    assert state == "RED"


@pytest.mark.unit
def test_performance_regression_triggers_yellow():
    """When performance_delta < -SAFETY_MODE_PERFORMANCE_DELTA, state is YELLOW with performance_regression."""
    now = time.time()
    snap = {
        "error_count_5m": 0,
        "not_enough_games_failures_30m": 0,
        "last_successful_odds_refresh_at": now,
        "last_successful_games_refresh_at": now,
        "estimated_api_calls_today": 10,
        "generation_failures_5m": 0,
        "api_failures_30m": 0,
        "performance_delta": -0.08,
    }
    with patch("app.core.safety_mode.telemetry_module.get_snapshot", return_value=snap):
        with patch("app.core.safety_mode.settings") as mock_settings:
            mock_settings.safety_mode_enabled = True
            mock_settings.safety_mode_red_error_count_5m = 25
            mock_settings.safety_mode_red_not_enough_games_30m = 10
            mock_settings.safety_mode_stale_odds_seconds = 900
            mock_settings.safety_mode_stale_games_seconds = 3600
            mock_settings.safety_mode_yellow_api_budget_ratio = 0.80
            mock_settings.safety_mode_yellow_gen_failures_5m = 10
            mock_settings.safety_mode_yellow_api_failures_30m = 15
            mock_settings.safety_mode_performance_delta = 0.05
            mock_settings.apisports_daily_quota = 100
            state = get_safety_state()
            assert state == "YELLOW"
            full = get_safety_snapshot()
            assert full["state"] == "YELLOW"
            assert "performance_regression" in full["reasons"] or full["telemetry"].get("performance_delta") == -0.08


@pytest.mark.unit
def test_correlation_penalty_applies_tighter_cap_and_policy_string():
    """When correlation_risk is in reasons, apply_degraded_policy caps to 3 and returns correlation_penalty."""
    with patch("app.core.safety_mode.get_safety_state", return_value="YELLOW"):
        with patch(
            "app.core.safety_mode.get_safety_snapshot",
            return_value={"state": "YELLOW", "reasons": ["correlation_risk"], "telemetry": {}, "events": []},
        ):
            out, policies = apply_degraded_policy({"num_legs": 5, "risk_profile": "balanced"})
    assert out["num_legs"] == 3
    assert "correlation_penalty" in policies


@pytest.mark.unit
def test_green_unchanged_when_v12_metrics_missing():
    """With healthy telemetry and no v1.2 keys, state remains GREEN."""
    now = time.time()
    healthy_snap = {
        "error_count_5m": 0,
        "not_enough_games_failures_30m": 0,
        "last_successful_odds_refresh_at": now,
        "last_successful_games_refresh_at": now,
        "estimated_api_calls_today": 10,
        "generation_failures_5m": 0,
        "api_failures_30m": 0,
    }
    with patch("app.core.safety_mode.telemetry_module.get_snapshot", return_value=healthy_snap):
        with patch("app.core.safety_mode.settings") as mock_settings:
            mock_settings.safety_mode_enabled = True
            mock_settings.safety_mode_red_error_count_5m = 25
            mock_settings.safety_mode_red_not_enough_games_30m = 10
            mock_settings.safety_mode_stale_odds_seconds = 900
            mock_settings.safety_mode_stale_games_seconds = 3600
            mock_settings.safety_mode_yellow_api_budget_ratio = 0.80
            mock_settings.safety_mode_yellow_gen_failures_5m = 10
            mock_settings.safety_mode_yellow_api_failures_30m = 15
            mock_settings.safety_mode_high_conf_max_loss_rate = 0.55
            mock_settings.safety_mode_performance_delta = 0.05
            mock_settings.safety_mode_correlation_legs_threshold = 5
            mock_settings.apisports_daily_quota = 100
            state = get_safety_state()
    assert state == "GREEN"
