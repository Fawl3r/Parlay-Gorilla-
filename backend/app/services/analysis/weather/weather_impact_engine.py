"""Deterministic weather impact modifiers for NFL, MLB, Soccer. Indoor/dome = no-op."""

from __future__ import annotations

from typing import Any, Dict, List


class WeatherImpactEngine:
    """
    Compute weather_efficiency_modifier, weather_volatility_modifier,
    weather_confidence_modifier, why, rules_fired from sport + weather dict.
    """

    @staticmethod
    def compute(sport: str, weather: Dict[str, Any] | None) -> Dict[str, Any]:
        """
        Returns dict with:
        - weather_efficiency_modifier (float, ~1.0 = no change)
        - weather_volatility_modifier (float)
        - weather_confidence_modifier (float)
        - why (str)
        - rules_fired (list of str)
        """
        sport_lower = (sport or "").strip().lower()
        if sport_lower not in ("nfl", "mlb", "soccer"):
            return _neutral_block("Sport not weather-adjusted.")

        if not weather or not isinstance(weather, dict):
            return _missing_weather_block(sport_lower)

        is_outdoor = weather.get("is_outdoor", True)
        if not is_outdoor:
            return _neutral_block("Indoor/dome; weather has no effect.")

        # Normalize numeric fields
        temp = _float(weather.get("temperature") or weather.get("temp"), 70.0)
        wind = _float(weather.get("wind_speed") or weather.get("wind"), 0.0)
        precip = _float(weather.get("precipitation") or weather.get("precip"), 0.0)
        condition = (weather.get("condition") or weather.get("description") or "").lower()

        if sport_lower == "nfl":
            return _nfl_rules(temp=temp, wind=wind, precip=precip, condition=condition)
        if sport_lower == "mlb":
            return _mlb_rules(temp=temp, wind=wind, precip=precip, condition=condition)
        if sport_lower == "soccer":
            return _soccer_rules(temp=temp, wind=wind, precip=precip, condition=condition)

        return _neutral_block("No rules applied.")


def _float(v: Any, default: float) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _neutral_block(why: str) -> Dict[str, Any]:
    return {
        "weather_efficiency_modifier": 1.0,
        "weather_volatility_modifier": 1.0,
        "weather_confidence_modifier": 1.0,
        "why": why,
        "rules_fired": [],
    }


def _missing_weather_block(sport: str) -> Dict[str, Any]:
    return {
        "weather_efficiency_modifier": 1.0,
        "weather_volatility_modifier": 1.0,
        "weather_confidence_modifier": 0.95,
        "why": "Weather data missing; confidence slightly reduced.",
        "rules_fired": ["weather_missing"],
    }


def _nfl_rules(
    temp: float, wind: float, precip: float, condition: str
) -> Dict[str, Any]:
    rules: List[str] = []
    eff_mod = 1.0
    vol_mod = 1.0
    conf_mod = 1.0
    why_bits: List[str] = []

    if wind > 15:
        rules.append("nfl_wind_high")
        eff_mod *= 0.92
        vol_mod *= 1.15
        why_bits.append("High wind reduces passing efficiency and increases variance.")
    if precip > 0 or "rain" in condition or "snow" in condition:
        rules.append("nfl_precip")
        eff_mod *= 0.90
        vol_mod *= 1.10
        why_bits.append("Precipitation affects ball handling and scoring.")
    if temp < 40:
        rules.append("nfl_cold")
        eff_mod *= 0.95
        why_bits.append("Cold can affect kicking and ball security.")

    if not rules:
        return _neutral_block("NFL outdoor conditions within normal range.")

    return {
        "weather_efficiency_modifier": round(eff_mod, 4),
        "weather_volatility_modifier": round(vol_mod, 4),
        "weather_confidence_modifier": round(conf_mod, 4),
        "why": " ".join(why_bits) if why_bits else "Weather impacts NFL gameplay.",
        "rules_fired": rules,
    }


def _mlb_rules(
    temp: float, wind: float, precip: float, condition: str
) -> Dict[str, Any]:
    rules: List[str] = []
    eff_mod = 1.0
    vol_mod = 1.0
    conf_mod = 1.0
    why_bits: List[str] = []

    # Warm + wind out → favor offense (efficiency up)
    if temp >= 75 and wind > 8:
        rules.append("mlb_warm_wind_out")
        eff_mod *= 1.05
        why_bits.append("Warm weather with wind out favors offense.")
    # Cold + wind in → favor pitchers
    elif temp < 60 and wind > 5:
        rules.append("mlb_cold_wind_in")
        eff_mod *= 0.92
        why_bits.append("Cold with wind in suppresses scoring.")
    if precip > 0 or "rain" in condition:
        rules.append("mlb_rain_risk")
        eff_mod *= 0.88
        conf_mod *= 0.92
        why_bits.append("Rain risk affects playability and confidence.")

    if not rules:
        return _neutral_block("MLB outdoor conditions within normal range.")

    return {
        "weather_efficiency_modifier": round(eff_mod, 4),
        "weather_volatility_modifier": round(vol_mod, 4),
        "weather_confidence_modifier": round(conf_mod, 4),
        "why": " ".join(why_bits) if why_bits else "Weather impacts MLB.",
        "rules_fired": rules,
    }


def _soccer_rules(
    temp: float, wind: float, precip: float, condition: str
) -> Dict[str, Any]:
    rules: List[str] = []
    eff_mod = 1.0
    vol_mod = 1.0
    conf_mod = 1.0
    why_bits: List[str] = []

    if "rain" in condition and (precip > 0.5 or "heavy" in condition or "thunder" in condition):
        rules.append("soccer_heavy_rain")
        eff_mod *= 0.88
        vol_mod *= 1.12
        why_bits.append("Heavy rain affects passing and shot accuracy.")
    elif precip > 0 or "rain" in condition:
        rules.append("soccer_rain")
        eff_mod *= 0.95
        vol_mod *= 1.05
    if temp > 90:
        rules.append("soccer_heat")
        eff_mod *= 0.92
        why_bits.append("Extreme heat affects stamina and pace.")
    if wind > 15:
        rules.append("soccer_wind")
        vol_mod *= 1.10
        why_bits.append("Strong wind affects long balls and set pieces.")

    if not rules:
        return _neutral_block("Soccer outdoor conditions within normal range.")

    return {
        "weather_efficiency_modifier": round(eff_mod, 4),
        "weather_volatility_modifier": round(vol_mod, 4),
        "weather_confidence_modifier": round(conf_mod, 4),
        "why": " ".join(why_bits) if why_bits else "Weather impacts soccer.",
        "rules_fired": rules,
    }
