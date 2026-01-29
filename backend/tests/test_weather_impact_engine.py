"""Deterministic unit tests for WeatherImpactEngine (NFL, MLB, Soccer)."""

import pytest

from app.services.analysis.weather.weather_impact_engine import WeatherImpactEngine


def test_nfl_wind_only():
    out = WeatherImpactEngine.compute(
        "nfl",
        {"is_outdoor": True, "wind_speed": 20, "temperature": 70, "precipitation": 0, "condition": "clear"},
    )
    assert out["weather_efficiency_modifier"] < 1.0
    assert out["weather_volatility_modifier"] > 1.0
    assert "nfl_wind_high" in out["rules_fired"]


def test_nfl_rain_wind():
    out = WeatherImpactEngine.compute(
        "nfl",
        {"is_outdoor": True, "wind_speed": 18, "temperature": 45, "precipitation": 5, "condition": "rain"},
    )
    assert out["weather_efficiency_modifier"] < 1.0
    assert "nfl_precip" in out["rules_fired"]


def test_nfl_cold():
    out = WeatherImpactEngine.compute(
        "nfl",
        {"is_outdoor": True, "wind_speed": 5, "temperature": 35, "precipitation": 0, "condition": "clear"},
    )
    assert out["weather_efficiency_modifier"] < 1.0
    assert "nfl_cold" in out["rules_fired"]


def test_nfl_indoor_no_op():
    out = WeatherImpactEngine.compute(
        "nfl",
        {"is_outdoor": False, "wind_speed": 20, "temperature": 70},
    )
    assert out["weather_efficiency_modifier"] == 1.0
    assert out["weather_volatility_modifier"] == 1.0
    assert out["rules_fired"] == []


def test_mlb_warm_wind_out():
    out = WeatherImpactEngine.compute(
        "mlb",
        {"is_outdoor": True, "wind_speed": 12, "temperature": 78, "precipitation": 0, "condition": "clear"},
    )
    assert out["weather_efficiency_modifier"] > 1.0
    assert "mlb_warm_wind_out" in out["rules_fired"]


def test_mlb_cold_wind_in():
    out = WeatherImpactEngine.compute(
        "mlb",
        {"is_outdoor": True, "wind_speed": 8, "temperature": 55, "precipitation": 0, "condition": "clear"},
    )
    assert out["weather_efficiency_modifier"] < 1.0
    assert "mlb_cold_wind_in" in out["rules_fired"]


def test_soccer_heavy_rain():
    out = WeatherImpactEngine.compute(
        "soccer",
        {"is_outdoor": True, "wind_speed": 10, "temperature": 60, "precipitation": 10, "condition": "heavy rain"},
    )
    assert out["weather_efficiency_modifier"] < 1.0
    assert out["weather_volatility_modifier"] > 1.0
    assert "soccer_heavy_rain" in out["rules_fired"]


def test_soccer_indoor_no_op():
    out = WeatherImpactEngine.compute(
        "soccer",
        {"is_outdoor": False, "wind_speed": 25, "temperature": 90},
    )
    assert out["weather_efficiency_modifier"] == 1.0
    assert out["rules_fired"] == []


def test_nfl_missing_weather():
    out = WeatherImpactEngine.compute("nfl", None)
    assert out["weather_confidence_modifier"] < 1.0
    assert "weather_missing" in out["rules_fired"]
