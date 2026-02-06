"""Build ConfidenceResult from breakdown: availability, score, blockers."""

from __future__ import annotations

from typing import Any, Dict

from app.schemas.confidence import (
    ConfidenceBlocker,
    ConfidenceComponents,
    ConfidenceResult,
)
from app.services.confidence.rules import is_weather_applicable


# Minimum data_quality to consider quality signals present; below this we mark DATA_QUALITY_TOO_LOW and likely unavailable
MIN_DATA_QUALITY_FOR_AVAILABILITY = 1.0


class ConfidenceResultBuilder:
    """
    Builds ConfidenceResult from ConfidenceBreakdownBuilder output.
    Availability: (statistical_edge + data_quality >= 5), data_quality >= 1 (quality signals present),
    and at least one of (market_agreement or situational_edge).
    If only weather missing and sport applicable, add WEATHER_UNAVAILABLE blocker but do not fail availability.
    """

    @staticmethod
    def build(
        *,
        confidence_breakdown: Dict[str, Any],
        sport: str = "",
        matchup_data: Dict[str, Any] | None = None,
    ) -> ConfidenceResult:
        """
        Build ConfidenceResult from breakdown dict.
        confidence_breakdown must have market_agreement, statistical_edge, situational_edge, data_quality, confidence_total.
        matchup_data optional: if provided, used to add WEATHER_UNAVAILABLE when weather applicable but missing.
        """
        ma = float(confidence_breakdown.get("market_agreement", 0))
        se = float(confidence_breakdown.get("statistical_edge", 0))
        si = float(confidence_breakdown.get("situational_edge", 0))
        dq = float(confidence_breakdown.get("data_quality", 0))
        total = float(confidence_breakdown.get("confidence_total", 0))

        components = ConfidenceComponents(
            market_agreement=ma,
            statistical_edge=se,
            situational_edge=si,
            data_quality=dq,
        )

        blockers: list[ConfidenceBlocker] = []
        has_stat_plus_quality = (se + dq) >= 5.0
        has_quality_signals = dq >= MIN_DATA_QUALITY_FOR_AVAILABILITY
        has_market_or_situational = ma >= 1.0 or si >= 1.0
        confidence_available = (
            has_stat_plus_quality and has_quality_signals and has_market_or_situational
        )

        if not confidence_available:
            if ma < 1.0:
                blockers.append(ConfidenceBlocker.MARKET_DATA_UNAVAILABLE)
            if se < 1.0:
                blockers.append(ConfidenceBlocker.STATS_UNAVAILABLE)
            if si < 1.0:
                blockers.append(ConfidenceBlocker.SITUATIONAL_DATA_UNAVAILABLE)
            if dq < MIN_DATA_QUALITY_FOR_AVAILABILITY:
                blockers.append(ConfidenceBlocker.DATA_QUALITY_TOO_LOW)
            if not blockers:
                blockers.append(ConfidenceBlocker.UNKNOWN)

        # If only weather missing and sport applicable, add blocker but do not fail availability
        if matchup_data is not None and sport:
            venue_is_dome = matchup_data.get("venue_is_dome") if isinstance(matchup_data.get("venue_is_dome"), bool) else None
            if is_weather_applicable(sport, venue_is_dome=venue_is_dome):
                weather = matchup_data.get("weather")
                if not weather or (isinstance(weather, dict) and not weather):
                    blockers.append(ConfidenceBlocker.WEATHER_UNAVAILABLE)

        return ConfidenceResult(
            confidence_available=confidence_available,
            confidence_score=round(total, 1) if confidence_available else None,
            components=components,
            blockers=blockers,
        )
