"""NFL adapter: normalize availability, efficiency, matchup from matchup_data."""

from __future__ import annotations

from typing import Any, Dict, List

from app.services.analysis.ugie_v2.adapters.base_adapter import (
    BaseUgieAdapter,
    NormalizedUgieInputs,
)


def _float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _get_stats(matchup_data: Dict[str, Any], side: str) -> Dict[str, Any]:
    key = f"{side}_team_stats"
    raw = matchup_data.get(key) or {}
    if not isinstance(raw, dict):
        return {}
    canonical = raw.get("canonical_stats") if isinstance(raw.get("canonical_stats"), dict) else raw
    return canonical if canonical else raw


def _get_injuries(matchup_data: Dict[str, Any], side: str) -> Dict[str, Any]:
    key = f"{side}_injuries"
    raw = matchup_data.get(key) or {}
    if not isinstance(raw, dict):
        return {}
    injury_json = raw.get("injury_json") if isinstance(raw.get("injury_json"), dict) else raw
    return injury_json if injury_json else raw


class NflAdapter(BaseUgieAdapter):
    """NFL: availability (injury impact), efficiency (strength/rating), matchup traits."""

    def normalize(self, matchup_data: Dict[str, Any], game: Any = None) -> NormalizedUgieInputs:
        out = NormalizedUgieInputs()

        home_inj = _get_injuries(matchup_data, "home")
        away_inj = _get_injuries(matchup_data, "away")
        home_impact = None
        away_impact = None
        if isinstance(home_inj, dict):
            home_impact = home_inj.get("impact_scores", {}).get("overall_impact") if isinstance(home_inj.get("impact_scores"), dict) else None
            home_impact = home_impact or home_inj.get("injury_severity_score")
        if isinstance(away_inj, dict):
            away_impact = away_inj.get("impact_scores", {}).get("overall_impact") if isinstance(away_inj.get("impact_scores"), dict) else None
            away_impact = away_impact or away_inj.get("injury_severity_score")

        if home_impact is not None and away_impact is not None:
            h, a = _float(home_impact), _float(away_impact)
            has_units = bool(
                home_inj.get("key_players_out") or home_inj.get("unit_counts")
                or away_inj.get("key_players_out") or away_inj.get("unit_counts")
            )
            out.availability = {
                "home_impact": h,
                "away_impact": a,
                "signals": [
                    {"key": "home_injury_impact", "value": h, "weight": 0.5, "direction": "home", "explain": (home_inj.get("impact_assessment") or "")[:200]},
                    {"key": "away_injury_impact", "value": a, "weight": 0.5, "direction": "away", "explain": (away_inj.get("impact_assessment") or "")[:200]},
                ],
                "confidence": 0.8 if has_units else 0.5,
                "why_summary": f"Injury impact home {h:.2f}, away {a:.2f}.",
            }
        else:
            out.missing.append("injuries")

        home_stats = _get_stats(matchup_data, "home")
        away_stats = _get_stats(matchup_data, "away")
        home_rating = (home_stats.get("strength_ratings") or {}).get("overall_rating") if isinstance(home_stats.get("strength_ratings"), dict) else home_stats.get("overall_rating")
        away_rating = (away_stats.get("strength_ratings") or {}).get("overall_rating") if isinstance(away_stats.get("strength_ratings"), dict) else away_stats.get("overall_rating")
        if home_rating is not None and away_rating is not None:
            h, a = _float(home_rating), _float(away_rating)
            out.efficiency = {
                "home_rating": h,
                "away_rating": a,
                "signals": [
                    {"key": "home_overall_rating", "value": h, "weight": 0.5, "direction": "home", "explain": "Overall strength"},
                    {"key": "away_overall_rating", "value": a, "weight": 0.5, "direction": "away", "explain": "Overall strength"},
                ],
                "confidence": 0.85,
                "why_summary": f"Home rating {h:.1f}, away {a:.1f}.",
            }
        else:
            out.missing.append("team_stats")

        return out
