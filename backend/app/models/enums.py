"""Shared enums for domain models."""

from enum import Enum


class SeasonState(str, Enum):
    """Season phase for a sport (used for candidate window lookahead and refresh TTL)."""
    OFF_SEASON = "off_season"
    PRESEASON = "preseason"
    IN_SEASON = "in_season"
    POSTSEASON = "postseason"
