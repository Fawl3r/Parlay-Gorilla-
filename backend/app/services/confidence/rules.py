"""Sport-aware rules for confidence: weather applicability, etc."""

from __future__ import annotations

INDOOR_SPORTS = {"NBA", "WNBA", "NHL"}
MOSTLY_INDOOR = {"UFC", "BOXING"}
OUTDOOR_SPORTS = {"NFL", "NCAAF", "MLB", "MLS", "EPL", "SOCCER"}


def is_weather_applicable(sport: str, venue_is_dome: bool | None = None) -> bool:
    """True if weather should influence confidence for this sport/venue."""
    s = (sport or "").upper()
    if s in INDOOR_SPORTS or s in MOSTLY_INDOOR:
        return False
    if venue_is_dome is True:
        return False
    return s in OUTDOOR_SPORTS
