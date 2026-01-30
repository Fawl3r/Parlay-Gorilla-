from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.services.analysis.article_player_reference_sanitizer import (
    ArticlePlayerReferenceSanitizer,
)
from app.services.analysis.role_language_sanitizer import RoleLanguageSanitizer


@dataclass(frozen=True)
class AnalysisContentNormalizer:
    """
    Normalizes persisted `analysis_content` payloads for backwards compatibility.

    Older `GameAnalysis.analysis_content` rows may be missing required keys. The
    frontend expects a fully-populated `GameAnalysisContent` object; if fields are
    missing, React components can crash and render as blank sections.

    This normalizer is intentionally conservative: it only fills missing/invalid
    fields with safe defaults and does not attempt any expensive recomputation.
    """

    def normalize(self, content: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = dict(content or {})

        # Optional headline fields
        if "headline" in normalized and normalized["headline"] is not None:
            normalized["headline"] = str(normalized["headline"])
        if "subheadline" in normalized and normalized["subheadline"] is not None:
            normalized["subheadline"] = str(normalized["subheadline"])

        normalized["opening_summary"] = str(normalized.get("opening_summary") or "")
        normalized["offensive_matchup_edges"] = self._normalize_matchup_edges(
            normalized.get("offensive_matchup_edges")
        )
        normalized["defensive_matchup_edges"] = self._normalize_matchup_edges(
            normalized.get("defensive_matchup_edges")
        )
        normalized["key_stats"] = self._normalize_string_list(normalized.get("key_stats"))
        normalized["ats_trends"] = self._normalize_trend_analysis(normalized.get("ats_trends"))
        normalized["totals_trends"] = self._normalize_trend_analysis(normalized.get("totals_trends"))
        normalized["weather_considerations"] = str(normalized.get("weather_considerations") or "")

        weather_data = normalized.get("weather_data")
        if weather_data is not None and not isinstance(weather_data, dict):
            normalized["weather_data"] = None

        normalized["model_win_probability"] = self._normalize_model_win_probability(
            normalized.get("model_win_probability")
        )
        normalized["ai_spread_pick"] = self._normalize_pick(normalized.get("ai_spread_pick"))
        normalized["ai_total_pick"] = self._normalize_pick(normalized.get("ai_total_pick"))
        normalized["best_bets"] = self._normalize_best_bets(normalized.get("best_bets"))
        normalized["same_game_parlays"] = self._normalize_same_game_parlays(
            normalized.get("same_game_parlays")
        )
        raw_article = str(normalized.get("full_article") or "")
        raw_article = ArticlePlayerReferenceSanitizer().sanitize(raw_article)
        neutralized, _ = RoleLanguageSanitizer().sanitize(raw_article)
        normalized["full_article"] = neutralized

        return normalized

    @staticmethod
    def _normalize_string_list(value: Any) -> List[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if item is not None]

    @staticmethod
    def _normalize_matchup_edges(value: Any) -> Dict[str, str]:
        if not isinstance(value, dict):
            return {"home_advantage": "", "away_advantage": "", "key_matchup": ""}
        return {
            "home_advantage": str(value.get("home_advantage") or ""),
            "away_advantage": str(value.get("away_advantage") or ""),
            "key_matchup": str(value.get("key_matchup") or ""),
        }

    @staticmethod
    def _normalize_trend_analysis(value: Any) -> Dict[str, str]:
        if not isinstance(value, dict):
            return {"home_team_trend": "", "away_team_trend": "", "analysis": ""}
        return {
            "home_team_trend": str(value.get("home_team_trend") or ""),
            "away_team_trend": str(value.get("away_team_trend") or ""),
            "analysis": str(value.get("analysis") or ""),
        }

    @staticmethod
    def _normalize_model_win_probability(value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            return AnalysisContentNormalizer._fallback_model_win_probability()

        try:
            home = float(value.get("home_win_prob")) if value.get("home_win_prob") is not None else None
            away = float(value.get("away_win_prob")) if value.get("away_win_prob") is not None else None
        except Exception:
            home, away = None, None

        if home is None or away is None:
            return AnalysisContentNormalizer._fallback_model_win_probability()

        explanation = str(value.get("explanation") or "")
        result: Dict[str, Any] = {
            "home_win_prob": float(home),
            "away_win_prob": float(away),
            "explanation": explanation,
        }

        # Optional fields used by the UI.
        if value.get("ai_confidence") is not None:
            try:
                result["ai_confidence"] = float(value.get("ai_confidence"))
            except Exception:
                pass
        if value.get("calculation_method") is not None:
            result["calculation_method"] = str(value.get("calculation_method"))
        if value.get("score_projection") is not None:
            result["score_projection"] = str(value.get("score_projection"))

        return result

    @staticmethod
    def _fallback_model_win_probability() -> Dict[str, Any]:
        return {
            "home_win_prob": 0.52,
            "away_win_prob": 0.48,
            "explanation": "Win probability unavailable (fallback applied).",
            "ai_confidence": 15.0,
            "calculation_method": "fallback",
        }

    @staticmethod
    def _normalize_pick(value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            return {"pick": "", "confidence": 0.0, "rationale": ""}
        try:
            confidence = float(value.get("confidence") or 0.0)
        except Exception:
            confidence = 0.0
        return {
            "pick": str(value.get("pick") or ""),
            "confidence": confidence,
            "rationale": str(value.get("rationale") or ""),
        }

    @staticmethod
    def _normalize_best_bets(value: Any) -> List[Dict[str, Any]]:
        if not isinstance(value, list):
            return []

        bets: List[Dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            try:
                confidence = float(item.get("confidence") or 0.0)
            except Exception:
                confidence = 0.0
            bets.append(
                {
                    "bet_type": str(item.get("bet_type") or ""),
                    "pick": str(item.get("pick") or ""),
                    "confidence": confidence,
                    "rationale": str(item.get("rationale") or ""),
                }
            )
        return bets

    @staticmethod
    def _normalize_same_game_parlays(value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            return AnalysisContentNormalizer._fallback_same_game_parlays()

        def _normalize_block(block: Any) -> Dict[str, Any]:
            if not isinstance(block, dict):
                return {"legs": [], "hit_probability": 0.0, "confidence": 0.0}
            try:
                hit_prob = float(block.get("hit_probability") or 0.0)
            except Exception:
                hit_prob = 0.0
            try:
                confidence = float(block.get("confidence") or 0.0)
            except Exception:
                confidence = 0.0
            legs = block.get("legs")
            if not isinstance(legs, list):
                legs = []
            return {"legs": legs, "hit_probability": hit_prob, "confidence": confidence}

        return {
            "safe_3_leg": _normalize_block(value.get("safe_3_leg")),
            "balanced_6_leg": _normalize_block(value.get("balanced_6_leg")),
            "degen_10_20_leg": _normalize_block(value.get("degen_10_20_leg")),
        }

    @staticmethod
    def _fallback_same_game_parlays() -> Dict[str, Any]:
        empty = {"legs": [], "hit_probability": 0.0, "confidence": 0.0}
        return {"safe_3_leg": dict(empty), "balanced_6_leg": dict(empty), "degen_10_20_leg": dict(empty)}


