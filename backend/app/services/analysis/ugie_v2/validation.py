"""UGIE v2 validation and clamping: never fail analysis generation."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

REQUIRED_UGIE_KEYS = ("pillars", "confidence_score", "risk_level", "data_quality", "recommended_action", "market_snapshot")
REQUIRED_PILLARS = ("availability", "efficiency", "matchup_fit", "script_stability", "market_alignment")
VALID_RISK = ("Low", "Medium", "High")
VALID_DQ_STATUS = ("Good", "Partial", "Poor")


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    if value != value:
        return lo
    return max(lo, min(hi, float(value)))


def validate_and_clamp_ugie_v2(ugie: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate ugie_v2 dict: ensure required keys, clamp numeric ranges.
    Returns the same dict (mutated in place) or a minimal valid dict if structure is broken.
    Never raises; never fail analysis generation.
    """
    if not isinstance(ugie, dict):
        return _minimal_valid_ugie()

    for key in REQUIRED_UGIE_KEYS:
        if key not in ugie:
            ugie[key] = _default_for_key(key)

    pillars = ugie.get("pillars")
    if not isinstance(pillars, dict):
        ugie["pillars"] = {p: _stub_pillar_dict(p) for p in REQUIRED_PILLARS}
        pillars = ugie["pillars"]
    for name in REQUIRED_PILLARS:
        if name not in pillars or not isinstance(pillars[name], dict):
            pillars[name] = _stub_pillar_dict(name)
        p = pillars[name]
        p["score"] = _clamp(float(p.get("score", 0.5)))
        p["confidence"] = _clamp(float(p.get("confidence", 0.0)))
        if "signals" not in p or not isinstance(p["signals"], list):
            p["signals"] = []
        if "top_edges" not in p or not isinstance(p["top_edges"], list):
            p["top_edges"] = []

    ugie["confidence_score"] = _clamp(float(ugie.get("confidence_score", 0.5)))
    risk = ugie.get("risk_level")
    if risk not in VALID_RISK:
        ugie["risk_level"] = "Medium"
    dq = ugie.get("data_quality")
    if not isinstance(dq, dict):
        ugie["data_quality"] = {"status": "Poor", "missing": ["data_quality"], "stale": [], "provider": ""}
        dq = ugie["data_quality"]
    if dq.get("status") not in VALID_DQ_STATUS:
        dq["status"] = "Partial"
    if "missing" not in dq or not isinstance(dq["missing"], list):
        dq["missing"] = []
    if "stale" not in dq or not isinstance(dq["stale"], list):
        dq["stale"] = []
    if "provider" not in dq:
        dq["provider"] = ""
    for key in ("roster", "injuries"):
        if key in dq and dq.get(key) not in ("ready", "stale", "missing"):
            del dq[key]

    if "recommended_action" not in ugie:
        ugie["recommended_action"] = ""
    if "market_snapshot" not in ugie or not isinstance(ugie["market_snapshot"], dict):
        ugie["market_snapshot"] = {}

    # --- Optional key_players: clamp and truncate; never raise ---
    kp = ugie.get("key_players")
    if kp is not None and isinstance(kp, dict):
        if kp.get("status") not in ("available", "limited", "unavailable"):
            kp["status"] = "unavailable"
        if "players" not in kp or not isinstance(kp["players"], list):
            kp["players"] = []
        for player in kp["players"]:
            if not isinstance(player, dict):
                continue
            player["confidence"] = _clamp(float(player.get("confidence", 0.5)))
            why = player.get("why")
            if isinstance(why, str) and len(why) > 200:
                player["why"] = why[:200].rsplit(" ", 1)[0] + "." if " " in why[:200] else why[:197] + "..."
            metrics = player.get("metrics")
            if metrics is not None and isinstance(metrics, list):
                safe = []
                for m in metrics[:3]:
                    if isinstance(m, dict):
                        label = str(m.get("label", m.get("name", "")))[:12]
                        value = str(m.get("value", m.get("stat", "")))[:16]
                        safe.append({"label": label, "value": value})
                player["metrics"] = safe

    return ugie


def _default_for_key(key: str) -> Any:
    if key == "pillars":
        return {p: _stub_pillar_dict(p) for p in REQUIRED_PILLARS}
    if key == "confidence_score":
        return 0.5
    if key == "risk_level":
        return "Medium"
    if key == "data_quality":
        return {"status": "Partial", "missing": [], "stale": [], "provider": ""}
    if key == "recommended_action":
        return ""
    if key == "market_snapshot":
        return {}
    return None


def _stub_pillar_dict(name: str) -> Dict[str, Any]:
    return {
        "score": 0.5,
        "confidence": 0.0,
        "signals": [],
        "why_summary": f"{name}: data_unavailable.",
        "top_edges": [],
    }


def _minimal_valid_ugie() -> Dict[str, Any]:
    return {
        "pillars": {p: _stub_pillar_dict(p) for p in REQUIRED_PILLARS},
        "confidence_score": 0.5,
        "risk_level": "Medium",
        "data_quality": {"status": "Poor", "missing": ["validation_failed"], "stale": [], "provider": ""},
        "recommended_action": "",
        "market_snapshot": {},
    }


def ugie_compact_summary(ugie: Dict[str, Any]) -> Dict[str, Any]:
    """Build a compact summary for logging (scores + confidence + data_quality)."""
    if not isinstance(ugie, dict):
        return {"error": "not_dict"}
    pillars = ugie.get("pillars") or {}
    scores = {}
    for name in REQUIRED_PILLARS:
        p = pillars.get(name)
        if isinstance(p, dict):
            scores[name] = round(float(p.get("score", 0.5)), 3)
        else:
            scores[name] = None
    dq = ugie.get("data_quality") or {}
    return {
        "confidence_score": round(float(ugie.get("confidence_score", 0.5)), 3),
        "risk_level": ugie.get("risk_level"),
        "data_quality_status": dq.get("status"),
        "data_quality_missing": dq.get("missing") or [],
        "pillar_scores": scores,
    }
