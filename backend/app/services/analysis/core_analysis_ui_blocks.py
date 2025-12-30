"""Decision-first UI copy blocks for the analysis detail page.

This module produces small, non-technical copy blocks used by the redesigned
analysis detail page. It must be:
- deterministic (no OpenAI required)
- resilient to missing inputs
- sport-agnostic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _clamp_pct(value: float) -> int:
    try:
        v = float(value)
    except Exception:
        v = 0.0
    if v < 0:
        return 0
    if v > 100:
        return 100
    return int(round(v))


def _confidence_level(pct: int) -> str:
    if pct >= 70:
        return "High"
    if pct >= 50:
        return "Medium"
    return "Low"


def _risk_level(*, ai_confidence_pct: int, home_prob: float, away_prob: float, limited_data: bool) -> str:
    # Close games tend to be higher risk.
    gap = abs((home_prob - away_prob) * 100.0)
    closeness = 100.0 - max(0.0, min(100.0, gap))

    # Weighted: confidence matters more than closeness.
    score = (100.0 - float(ai_confidence_pct)) * 0.7 + closeness * 0.3
    if limited_data:
        score = max(score, 55.0)

    if score >= 70.0:
        return "High"
    if score >= 45.0:
        return "Medium"
    return "Low"


def _sanitize(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return ""

    replacements = [
        ("Model confidence", "How sure the AI is"),
        ("model confidence", "how sure the AI is"),
        ("Expected Value (EV)", "Long-term value"),
        ("expected value (EV)", "long-term value"),
        ("Variance", "Risk"),
        ("variance", "risk"),
        ("Advanced metrics", "Deeper stats"),
        ("advanced metrics", "deeper stats"),
        ("model", "AI"),
    ]
    out = s
    for a, b in replacements:
        out = out.replace(a, b)

    return out.strip()


def _first_sentence(text: str, max_chars: int) -> str:
    s = _sanitize(text)
    if not s:
        return ""
    first = s.split(".")[0].strip()
    if not first:
        first = s
    if len(first) > max_chars:
        return (first[: max_chars - 1].rstrip() + "…").strip()
    return first


def _strip_percentages(text: str) -> str:
    import re

    s = _sanitize(text)
    if not s:
        return ""
    s = re.sub(r"\b\d+(?:\.\d+)?%\b", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


def _limit_words(text: str, max_words: int) -> str:
    parts = [p for p in str(text or "").split() if p]
    if len(parts) <= max_words:
        return " ".join(parts).strip()
    return (" ".join(parts[:max_words]) + "…").strip()


@dataclass(frozen=True)
class CoreAnalysisUiBlocksBuilder:
    sport_icon: str
    bet_tab_labels: Dict[str, str]
    unit_offense: str = "Offense"
    unit_defense: str = "Defense"

    @staticmethod
    def for_sport(sport: str) -> "CoreAnalysisUiBlocksBuilder":
        s = str(sport or "").lower().strip()
        # soccer family
        if s in {"mls", "epl", "laliga", "ucl", "soccer"}:
            return CoreAnalysisUiBlocksBuilder(
                sport_icon="⚽",
                bet_tab_labels={"h2h": "Moneyline", "spreads": "Spread", "totals": "Total"},
                unit_offense="Attack",
                unit_defense="Defense",
            )
        if s == "nhl":
            return CoreAnalysisUiBlocksBuilder(
                sport_icon="🏒",
                bet_tab_labels={"h2h": "Moneyline", "spreads": "Puck Line", "totals": "Total"},
            )
        if s == "mlb":
            return CoreAnalysisUiBlocksBuilder(
                sport_icon="⚾",
                bet_tab_labels={"h2h": "Moneyline", "spreads": "Run Line", "totals": "Total"},
                unit_offense="Batting",
                unit_defense="Pitching",
            )
        if s in {"nba", "ncaab"}:
            return CoreAnalysisUiBlocksBuilder(
                sport_icon="🏀",
                bet_tab_labels={"h2h": "Moneyline", "spreads": "Spread", "totals": "Total"},
            )
        if s in {"nfl", "ncaaf"}:
            return CoreAnalysisUiBlocksBuilder(
                sport_icon="🏈",
                bet_tab_labels={"h2h": "Moneyline", "spreads": "Spread", "totals": "Total"},
            )
        if s in {"ufc", "boxing"}:
            return CoreAnalysisUiBlocksBuilder(sport_icon="🥊", bet_tab_labels={"h2h": "Moneyline"})
        return CoreAnalysisUiBlocksBuilder(
            sport_icon="🏟️",
            bet_tab_labels={"h2h": "Moneyline", "spreads": "Spread", "totals": "Total"},
        )

    def build(
        self,
        *,
        home_team: str,
        away_team: str,
        model_probs: Dict[str, Any],
        opening_summary: str,
        spread_pick: Dict[str, Any],
        total_pick: Dict[str, Any],
        offensive_edges: Dict[str, Any],
        defensive_edges: Dict[str, Any],
        ats_trends: Dict[str, Any],
        totals_trends: Dict[str, Any],
        weather_considerations: str,
    ) -> Dict[str, Any]:
        home_prob = float(model_probs.get("home_win_prob") or 0.52)
        away_prob = float(model_probs.get("away_win_prob") or 0.48)
        favored_team, favored_pct = self._favored(home_team, away_team, home_prob, away_prob)

        ai_conf = _clamp_pct(float(model_probs.get("ai_confidence") or 50.0))
        limited_data = str(model_probs.get("calculation_method") or "").lower().strip() in {"fallback", "minimal_fallback"}
        risk_level = _risk_level(ai_confidence_pct=ai_conf, home_prob=home_prob, away_prob=away_prob, limited_data=limited_data)

        recommendation = self._recommendation(
            favored_team=favored_team,
            spread_pick=spread_pick,
            total_pick=total_pick,
        )
        why = _first_sentence(opening_summary, 240)

        key_drivers = self._key_drivers(
            offensive_edges=offensive_edges,
            defensive_edges=defensive_edges,
            risk_level=risk_level,
        )

        bet_options = self._bet_options(
            favored_team=favored_team,
            ai_confidence=ai_conf,
            risk_level=risk_level,
            spread_pick=spread_pick,
            total_pick=total_pick,
        )

        matchup_cards = self._matchup_cards(
            home_team=home_team,
            away_team=away_team,
            offensive_edges=offensive_edges,
            defensive_edges=defensive_edges,
        )

        trends = self._trends(
            ats_trends=ats_trends,
            totals_trends=totals_trends,
            weather_considerations=weather_considerations,
        )

        ui_quick_take = {
            "sport_icon": self.sport_icon,
            "favored_team": favored_team,
            "confidence_percent": favored_pct,
            "confidence_level": _confidence_level(ai_conf),
            "risk_level": risk_level,
            "recommendation": recommendation,
            "why": why,
        }

        if limited_data:
            ui_quick_take["limited_data_note"] = (
                "This matchup has limited historical data. The AI adjusted confidence accordingly."
            )

        return {
            "ui_quick_take": ui_quick_take,
            "ui_key_drivers": key_drivers,
            "ui_bet_options": bet_options,
            "ui_matchup_cards": matchup_cards,
            "ui_trends": trends,
        }

    @staticmethod
    def _favored(home_team: str, away_team: str, home_prob: float, away_prob: float) -> Tuple[str, int]:
        if home_prob >= away_prob:
            return str(home_team), _clamp_pct(home_prob * 100.0)
        return str(away_team), _clamp_pct(away_prob * 100.0)

    @staticmethod
    def _recommendation(*, favored_team: str, spread_pick: Dict[str, Any], total_pick: Dict[str, Any]) -> str:
        # One recommendation only. Prefer spread if it has high confidence, else ML.
        try:
            spread_conf = float(spread_pick.get("confidence") or 0.0)
        except Exception:
            spread_conf = 0.0
        spread_text = _sanitize(str(spread_pick.get("pick") or ""))
        if spread_text and spread_conf >= 60.0:
            return spread_text
        return f"{favored_team} ML" if favored_team else "No clear recommendation yet."

    def _key_drivers(
        self,
        *,
        offensive_edges: Dict[str, Any],
        defensive_edges: Dict[str, Any],
        risk_level: str,
    ) -> Dict[str, Any]:
        positives: List[str] = []

        for raw in [
            offensive_edges.get("key_matchup"),
            offensive_edges.get("home_advantage"),
            offensive_edges.get("away_advantage"),
            defensive_edges.get("key_matchup"),
        ]:
            text = _limit_words(_strip_percentages(str(raw or "")), 12)
            if text and text not in positives:
                positives.append(text)
            if len(positives) >= 2:
                break

        risk = "This game has higher volatility than average." if risk_level == "High" else "There are a few ways this can go sideways."
        risk = _limit_words(risk, 12)

        return {"positives": positives[:2], "risks": [risk]}

    def _bet_options(
        self,
        *,
        favored_team: str,
        ai_confidence: int,
        risk_level: str,
        spread_pick: Dict[str, Any],
        total_pick: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []

        out.append(
            {
                "id": "moneyline",
                "market_type": "h2h",
                "label": self.bet_tab_labels.get("h2h", "Moneyline"),
                "lean": f"{favored_team} ML" if favored_team else "No lean",
                "confidence_level": _confidence_level(ai_confidence),
                "risk_level": risk_level,
                "explanation": "Back the side the AI expects to win most often.",
            }
        )

        spread_text = _sanitize(str(spread_pick.get("pick") or ""))
        if spread_text:
            spread_conf = _clamp_pct(float(spread_pick.get("confidence") or ai_confidence))
            out.append(
                {
                    "id": "spread",
                    "market_type": "spreads",
                    "label": self.bet_tab_labels.get("spreads", "Spread"),
                    "lean": spread_text,
                    "confidence_level": _confidence_level(spread_conf),
                    "risk_level": risk_level,
                    "explanation": _first_sentence(str(spread_pick.get("rationale") or ""), 140)
                    or "This side fits the matchup edge.",
                }
            )

        total_text = _sanitize(str(total_pick.get("pick") or ""))
        if total_text:
            total_conf = _clamp_pct(float(total_pick.get("confidence") or ai_confidence))
            out.append(
                {
                    "id": "total",
                    "market_type": "totals",
                    "label": self.bet_tab_labels.get("totals", "Total"),
                    "lean": total_text,
                    "confidence_level": _confidence_level(total_conf),
                    "risk_level": risk_level,
                    "explanation": _first_sentence(str(total_pick.get("rationale") or ""), 140)
                    or "This total matches the expected game flow.",
                }
            )

        return out

    def _matchup_cards(
        self,
        *,
        home_team: str,
        away_team: str,
        offensive_edges: Dict[str, Any],
        defensive_edges: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        away = str(away_team or "").strip()
        home = str(home_team or "").strip()

        card1 = {
            "title": f"{away} {self.unit_offense} vs {home} {self.unit_defense}".strip(),
            "summary": _sanitize(str(offensive_edges.get("away_advantage") or offensive_edges.get("key_matchup") or "")),
            "bullets": [
                _sanitize(str(offensive_edges.get("key_matchup") or "")),
                _sanitize(str(defensive_edges.get("away_advantage") or "")),
            ],
        }
        card2 = {
            "title": f"{home} {self.unit_offense} vs {away} {self.unit_defense}".strip(),
            "summary": _sanitize(str(offensive_edges.get("home_advantage") or defensive_edges.get("key_matchup") or "")),
            "bullets": [
                _sanitize(str(defensive_edges.get("key_matchup") or "")),
                _sanitize(str(defensive_edges.get("home_advantage") or "")),
            ],
        }

        def _clean(card: Dict[str, Any]) -> Dict[str, Any]:
            bullets = [b for b in card.get("bullets", []) if str(b).strip()]
            return {"title": card.get("title", ""), "summary": card.get("summary", ""), "bullets": bullets[:3]}

        cards = [_clean(card1), _clean(card2)]
        return [c for c in cards if str(c.get("summary") or "").strip() or len(c.get("bullets") or []) > 0]

    @staticmethod
    def _trends(*, ats_trends: Dict[str, Any], totals_trends: Dict[str, Any], weather_considerations: str) -> List[str]:
        trends: List[str] = []
        for raw in [ats_trends.get("analysis"), totals_trends.get("analysis"), weather_considerations]:
            text = _limit_words(_strip_percentages(str(raw or "")), 15)
            if text:
                trends.append(text)
            if len(trends) >= 4:
                break
        return trends


