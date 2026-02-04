"""UGIE v2 builder: assemble five pillars + data_quality from existing analysis outputs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.event_logger import log_event
from app.services.analysis.ugie_v2.models import (
    UgieDataQuality,
    UgiePillar,
    UgieSignal,
    UgieV2,
)


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    if value != value:  # NaN
        return lo
    return max(lo, min(hi, value))


def _stub_pillar(name: str, missing_reason: str = "data_unavailable") -> UgiePillar:
    return UgiePillar(
        score=0.5,
        confidence=0.0,
        signals=[],
        why_summary=f"{name}: {missing_reason}.",
        top_edges=[],
    )


def get_minimal_ugie_v2(missing_reason: str = "ugie_v2_builder_error") -> Dict[str, Any]:
    """Return a minimal ugie_v2 dict for error fallback (never fail analysis generation)."""
    pillars = {
        name: _stub_pillar(name, missing_reason) for name in UgieV2Builder.PILLAR_NAMES
    }
    dq = UgieDataQuality(status="Poor", missing=[missing_reason], stale=[], provider="")
    ugie = UgieV2(
        pillars=pillars,
        confidence_score=0.5,
        risk_level="Medium",
        data_quality=dq,
        recommended_action="",
        market_snapshot={},
        weather=None,
    )
    return ugie.as_dict()


class UgieV2Builder:
    """Build ugie_v2 dict from existing draft, matchup_data, game, odds_snapshot, model_probs."""

    PILLAR_NAMES = ("availability", "efficiency", "matchup_fit", "script_stability", "market_alignment")

    @classmethod
    def build(
        cls,
        *,
        draft: Dict[str, Any],
        matchup_data: Dict[str, Any],
        game: Any,
        odds_snapshot: Dict[str, Any],
        model_probs: Dict[str, Any],
        weather_block: Optional[Dict[str, Any]] = None,
        allowed_player_names: Optional[List[str]] = None,
        allowlist_by_team: Optional[Dict[str, List[str]]] = None,
        positions_by_name: Optional[Dict[str, str]] = None,
        redaction_count: Optional[int] = None,
        updated_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Assemble ugie_v2 with five pillars, data_quality, recommended_action, market_snapshot.
        Uses existing draft keys and matchup_data; stubs missing inputs.
        """
        pillars: Dict[str, UgiePillar] = {}
        missing: List[str] = []
        stale: List[str] = []
        provider_parts: List[str] = []

        normalized = None
        try:
            from app.services.analysis.ugie_v2.adapters import get_adapter
            adapter = get_adapter(getattr(game, "sport", None) or "")
            if adapter:
                normalized = adapter.normalize(matchup_data, game)
        except Exception:
            normalized = None

        # --- Availability pillar (adapter or fallback) ---
        if normalized and normalized.availability:
            av = normalized.availability
            h = float(av.get("home_impact", 0))
            a = float(av.get("away_impact", 0))
            score = _clamp(0.5 + (a - h) * 0.5)
            conf = float(av.get("confidence", 0.5))
            sigs = av.get("signals") or []
            signals = [
                UgieSignal(s.get("key", ""), s.get("value", 0), float(s.get("weight", 0.5)), s.get("direction", ""), s.get("explain", ""))
                for s in sigs if isinstance(s, dict)
            ]
            pillars["availability"] = UgiePillar(score=score, confidence=conf, signals=signals, why_summary=(av.get("why_summary") or "")[:500], top_edges=[])
        else:
            home_inj = matchup_data.get("home_injuries") or {}
            away_inj = matchup_data.get("away_injuries") or {}
            if isinstance(home_inj, dict) and isinstance(away_inj, dict):
                home_impact = home_inj.get("impact_scores", {}).get("overall_impact") or home_inj.get("injury_severity_score")
                away_impact = away_inj.get("impact_scores", {}).get("overall_impact") or away_inj.get("injury_severity_score")
                if home_impact is not None and away_impact is not None:
                    try:
                        h = float(home_impact)
                        a = float(away_impact)
                        score = _clamp(0.5 + (a - h) * 0.5)
                        conf = 0.8 if (home_inj.get("key_players_out") or home_inj.get("unit_counts") or away_inj.get("key_players_out") or away_inj.get("unit_counts")) else 0.5
                        signals = [
                            UgieSignal("home_injury_impact", h, 0.5, "home", home_inj.get("impact_assessment") or ""),
                            UgieSignal("away_injury_impact", a, 0.5, "away", away_inj.get("impact_assessment") or ""),
                        ]
                        # Dedupe: avoid repeating "Unable to assess injury impact..." for home + away
                        home_why = (home_inj.get("impact_assessment") or "Injury data present.").strip()
                        away_why = (away_inj.get("impact_assessment") or "").strip()
                        parts = [home_why]
                        if away_why and away_why != home_why:
                            parts.append(away_why)
                        why = " ".join(parts)[:500]
                        pillars["availability"] = UgiePillar(score=score, confidence=conf, signals=signals, why_summary=why, top_edges=[])
                    except (TypeError, ValueError):
                        pillars["availability"] = _stub_pillar("availability", "invalid_injury_data")
                        missing.append("injuries")
                else:
                    pillars["availability"] = _stub_pillar("availability", "no_impact_scores")
                    missing.append("injuries")
            else:
                pillars["availability"] = _stub_pillar("availability", "no_injury_data")
                missing.append("injuries")

        # --- Efficiency pillar (adapter or fallback) ---
        if normalized and normalized.efficiency:
            ef = normalized.efficiency
            h = float(ef.get("home_rating", 0))
            a = float(ef.get("away_rating", 0))
            score = _clamp(0.5 + (h - a) * 0.02)
            conf = float(ef.get("confidence", 0.85))
            sigs = ef.get("signals") or []
            signals = [
                UgieSignal(s.get("key", ""), s.get("value", 0), float(s.get("weight", 0.5)), s.get("direction", ""), s.get("explain", ""))
                for s in sigs if isinstance(s, dict)
            ]
            pillars["efficiency"] = UgiePillar(score=score, confidence=conf, signals=signals, why_summary=(ef.get("why_summary") or "")[:500], top_edges=[])
        else:
            home_stats = matchup_data.get("home_team_stats") or {}
            away_stats = matchup_data.get("away_team_stats") or {}
            if isinstance(home_stats, dict) and isinstance(away_stats, dict):
                home_rating = (home_stats.get("strength_ratings") or {}).get("overall_rating")
                away_rating = (away_stats.get("strength_ratings") or {}).get("overall_rating")
                if home_rating is not None and away_rating is not None:
                    try:
                        h = float(home_rating)
                        a = float(away_rating)
                        score = _clamp(0.5 + (h - a) * 0.02)
                        conf = 0.85
                        signals = [
                            UgieSignal("home_overall_rating", h, 0.5, "home", "Overall strength"),
                            UgieSignal("away_overall_rating", a, 0.5, "away", "Overall strength"),
                        ]
                        why = f"Home rating {h:.1f}, away {a:.1f}."
                        pillars["efficiency"] = UgiePillar(score=score, confidence=conf, signals=signals, why_summary=why, top_edges=[])
                    except (TypeError, ValueError):
                        pillars["efficiency"] = _stub_pillar("efficiency", "invalid_stats")
                        missing.append("team_stats")
                else:
                    pillars["efficiency"] = _stub_pillar("efficiency", "no_ratings")
                    missing.append("team_stats")
            else:
                pillars["efficiency"] = _stub_pillar("efficiency", "no_team_stats")
                missing.append("team_stats")

        if normalized and normalized.missing:
            for m in normalized.missing:
                if m not in missing:
                    missing.append(m)

        # --- Matchup fit pillar ---
        off_edges = draft.get("offensive_matchup_edges") or {}
        def_edges = draft.get("defensive_matchup_edges") or {}
        top_edges: List[str] = []
        if isinstance(off_edges, dict):
            for k in ("home_advantage", "away_advantage", "key_matchup"):
                v = off_edges.get(k)
                if v and isinstance(v, str) and v.strip():
                    top_edges.append(v.strip()[:200])
        if isinstance(def_edges, dict):
            for k in ("home_advantage", "away_advantage", "key_matchup"):
                v = def_edges.get(k)
                if v and isinstance(v, str) and v.strip():
                    top_edges.append(v.strip()[:200])
        home_prob = float(model_probs.get("home_win_prob", 0.5))
        away_prob = float(model_probs.get("away_win_prob", 0.5))
        matchup_score = home_prob
        matchup_conf = 0.7 if top_edges else 0.4
        pillars["matchup_fit"] = UgiePillar(
            score=_clamp(matchup_score),
            confidence=matchup_conf,
            signals=[],
            why_summary=model_probs.get("explanation") or "Model matchup.",
            top_edges=top_edges[:5],
        )

        # --- Script stability pillar ---
        outcome_paths = draft.get("outcome_paths") or {}
        var_script = (outcome_paths.get("variance_upset_script") or {}) if isinstance(outcome_paths, dict) else {}
        var_prob = var_script.get("probability") if isinstance(var_script, dict) else None
        if var_prob is not None:
            try:
                v = float(var_prob)
                stability_score = 1.0 - v
                stability_score = _clamp(stability_score)
                pillars["script_stability"] = UgiePillar(
                    score=stability_score,
                    confidence=0.75,
                    signals=[UgieSignal("variance_upset_prob", v, 1.0, "volatility", var_script.get("description") or "")],
                    why_summary=(var_script.get("description") or "")[:300],
                    top_edges=[],
                )
            except (TypeError, ValueError):
                pillars["script_stability"] = _stub_pillar("script_stability", "invalid_outcome_paths")
        else:
            pillars["script_stability"] = _stub_pillar("script_stability", "no_outcome_paths")
            missing.append("outcome_paths")

        # --- Market alignment pillar ---
        conf_breakdown = draft.get("confidence_breakdown") or {}
        conf_total = conf_breakdown.get("confidence_total") if isinstance(conf_breakdown, dict) else None
        if conf_total is not None:
            try:
                ct = float(conf_total)
                score = _clamp(ct / 100.0)
                pillars["market_alignment"] = UgiePillar(
                    score=score,
                    confidence=0.8,
                    signals=[UgieSignal("confidence_total", ct, 1.0, "market", conf_breakdown.get("explanation") or "")],
                    why_summary=(conf_breakdown.get("explanation") or "")[:300],
                    top_edges=[],
                )
            except (TypeError, ValueError):
                pillars["market_alignment"] = _stub_pillar("market_alignment", "invalid_confidence_breakdown")
        else:
            ai_conf = model_probs.get("ai_confidence")
            if ai_conf is not None:
                try:
                    score = _clamp(float(ai_conf) / 100.0)
                    pillars["market_alignment"] = UgiePillar(score=score, confidence=0.5, signals=[], why_summary="From model confidence.", top_edges=[])
                except (TypeError, ValueError):
                    pillars["market_alignment"] = _stub_pillar("market_alignment", "invalid_ai_confidence")
            else:
                pillars["market_alignment"] = _stub_pillar("market_alignment", "no_confidence_data")

        # --- Data quality ---
        home_dq = matchup_data.get("home_data_quality") or {}
        away_dq = matchup_data.get("away_data_quality") or {}
        if isinstance(home_dq, dict):
            provider_parts.extend(home_dq.get("sources_used") or [])
        if isinstance(away_dq, dict):
            provider_parts.extend(away_dq.get("sources_used") or [])
        source_flags = list(matchup_data.get("home_source_flags") or []) + list(matchup_data.get("away_source_flags") or [])
        if source_flags:
            provider_parts.extend(source_flags)
        if not provider_parts:
            provider_parts = ["fallback"]
        provider = "mixed" if len(set(provider_parts)) > 1 else (provider_parts[0] if provider_parts else "fallback")
        sport = (getattr(game, "sport", None) or "").strip().lower()
        if sport in ("nfl", "mlb", "soccer") and not matchup_data.get("weather"):
            missing.append("weather")
        if missing:
            status = "Poor" if len(missing) > 2 else "Partial"
        else:
            status = "Good"
        data_quality = UgieDataQuality(status=status, missing=missing, stale=stale, provider=provider)

        # --- Apply weather modifiers to efficiency and script_stability pillars ---
        if weather_block:
            w_eff = float(weather_block.get("weather_efficiency_modifier", 1.0))
            w_vol = float(weather_block.get("weather_volatility_modifier", 1.0))
            if "efficiency" in pillars:
                p = pillars["efficiency"]
                pillars["efficiency"] = UgiePillar(
                    score=_clamp(p.score * w_eff),
                    confidence=p.confidence,
                    signals=p.signals,
                    why_summary=p.why_summary,
                    top_edges=p.top_edges,
                )
            if "script_stability" in pillars and w_vol > 0:
                p = pillars["script_stability"]
                pillars["script_stability"] = UgiePillar(
                    score=_clamp(p.score / w_vol),
                    confidence=p.confidence,
                    signals=p.signals,
                    why_summary=p.why_summary,
                    top_edges=p.top_edges,
                )

        # --- Overall confidence and risk ---
        ai_conf = model_probs.get("ai_confidence")
        if ai_conf is not None:
            try:
                conf_score = _clamp(float(ai_conf) / 100.0)
            except (TypeError, ValueError):
                conf_score = 0.5
        else:
            conf_score = 0.5
        if conf_score < 0.4:
            risk_level = "High"
        elif conf_score > 0.6:
            risk_level = "Low"
        else:
            risk_level = "Medium"
        if weather_block:
            w_conf = weather_block.get("weather_confidence_modifier")
            if w_conf is not None:
                try:
                    conf_score = _clamp(conf_score * float(w_conf))
                except (TypeError, ValueError):
                    pass
        ugie_weather = None
        if weather_block:
            from app.services.analysis.ugie_v2.models import UgieWeatherBlock
            ugie_weather = UgieWeatherBlock(
                weather_efficiency_modifier=float(weather_block.get("weather_efficiency_modifier", 1.0)),
                weather_volatility_modifier=float(weather_block.get("weather_volatility_modifier", 1.0)),
                weather_confidence_modifier=float(weather_block.get("weather_confidence_modifier", 1.0)),
                why=weather_block.get("why") or "",
                rules_fired=weather_block.get("rules_fired") or [],
            )

        # --- Recommended action ---
        best_bets = draft.get("best_bets") or []
        if isinstance(best_bets, list) and best_bets:
            b = best_bets[0]
            if isinstance(b, dict):
                rec = (b.get("pick") or "") + ": " + (b.get("rationale") or "")[:200]
            else:
                rec = str(b)[:300]
        else:
            sp = draft.get("ai_spread_pick") or {}
            tp = draft.get("ai_total_pick") or {}
            rec = (sp.get("pick") or "") + " / " + (tp.get("pick") or "") + " (spread/total)"
        recommended_action = rec[:500] if rec else "See picks."

        # --- Market snapshot ---
        market_snapshot = {
            "spread": odds_snapshot.get("home_spread_point"),
            "total": odds_snapshot.get("total_line"),
            "home_ml": odds_snapshot.get("home_ml"),
            "away_ml": odds_snapshot.get("away_ml"),
        }

        # --- Key players (optional; never fail analysis) ---
        key_players_block = None
        try:
            from app.services.analysis.ugie_v2.key_players_builder import KeyPlayersBuilder
            sport = (getattr(game, "sport", None) or "").strip().lower()
            key_players_block = KeyPlayersBuilder().build(
                game=game,
                sport=sport,
                matchup_data=matchup_data,
                allowed_player_names=allowed_player_names,
                allowlist_by_team=allowlist_by_team,
                positions_by_name=positions_by_name,
                updated_at=updated_at,
            )
            home_count = sum(1 for p in key_players_block.players if p.team == "home")
            away_count = sum(1 for p in key_players_block.players if p.team == "away")
            updated_at_age_hours = None
            if key_players_block.updated_at:
                try:
                    ts = datetime.fromisoformat(
                        key_players_block.updated_at.replace("Z", "+00:00")
                    )
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    updated_at_age_hours = (datetime.now(timezone.utc) - ts).total_seconds() / 3600.0
                except (ValueError, TypeError):
                    pass
            _kp_log = logging.getLogger(__name__)
            log_event(
                _kp_log,
                "key_players_built",
                level=logging.INFO,
                status=key_players_block.status,
                reason=key_players_block.reason,
                home_count=home_count,
                away_count=away_count,
                updated_at_age_hours=updated_at_age_hours,
            )
        except Exception:
            key_players_block = None

        ugie = UgieV2(
            pillars=pillars,
            confidence_score=conf_score,
            risk_level=risk_level,
            data_quality=data_quality,
            recommended_action=recommended_action,
            market_snapshot=market_snapshot,
            weather=ugie_weather,
            key_players=key_players_block,
        )
        return ugie.as_dict()
