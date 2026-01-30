"""Shared analysis payload contract helpers.

These helpers define what "core analysis" means for the frontend and for SEO.
They also provide small utilities for merging and marking generation status.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


CORE_REQUIRED_KEYS = (
    "opening_summary",
    "ats_trends",
    "totals_trends",
    "ai_spread_pick",
    "ai_total_pick",
    "best_bets",
    "model_win_probability",
    "confidence_breakdown",
)


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def is_placeholder_opening_summary(opening_summary: str) -> bool:
    return "analysis is being prepared" in (opening_summary or "").lower()


def is_core_ready(content: Dict[str, Any]) -> bool:
    """Return True when the analysis has the minimum fields to render the page."""
    try:
        for key in CORE_REQUIRED_KEYS:
            if key not in content:
                return False
    except Exception:
        return False

    opening = str(content.get("opening_summary") or "")
    if is_placeholder_opening_summary(opening):
        return False

    spread_pick = content.get("ai_spread_pick") or {}
    total_pick = content.get("ai_total_pick") or {}
    ats = content.get("ats_trends") or {}
    totals = content.get("totals_trends") or {}

    has_picks = bool(getattr(spread_pick, "get", None) and spread_pick.get("pick")) and bool(
        getattr(total_pick, "get", None) and total_pick.get("pick")
    )
    has_trends = bool(getattr(ats, "get", None) and ats.get("analysis")) and bool(
        getattr(totals, "get", None) and totals.get("analysis")
    )
    if not (has_picks and has_trends):
        return False

    # Require at least one best bet so the UI can render the "Top 3 Best Bets" section.
    # Older stored payloads sometimes had an empty list even when picks/trends existed.
    best_bets = content.get("best_bets")
    if not isinstance(best_bets, list) or len(best_bets) == 0:
        return False

    # Guardrail: if stored trend strings contain impossible percentages or obviously stale/mismatched
    # availability, treat core as NOT ready so the orchestrator regenerates the core payload.
    #
    # This fixes historical bugs like "10000.0% cover rate" being persisted in `game_analyses`.
    ats_home = str(ats.get("home_team_trend") or "")
    ats_away = str(ats.get("away_team_trend") or "")
    tot_home = str(totals.get("home_team_trend") or "")
    tot_away = str(totals.get("away_team_trend") or "")

    if _trend_strings_have_impossible_percentages([ats_home, ats_away, tot_home, tot_away]):
        return False

    if _trend_strings_have_mismatched_availability(home=ats_home, away=ats_away):
        return False
    if _trend_strings_have_mismatched_availability(home=tot_home, away=tot_away):
        return False

    # Require confidence_breakdown so the Confidence Breakdown meter shows for all sports.
    cb = content.get("confidence_breakdown")
    if not isinstance(cb, dict) or "confidence_total" not in cb:
        return False

    return True


def _trend_strings_have_impossible_percentages(trends: list[str]) -> bool:
    """Return True if any trend string includes a percentage > 100."""
    import re

    pct_re = re.compile(r"(\d+(?:\.\d+)?)%")
    for trend in trends:
        for match in pct_re.finditer(trend or ""):
            try:
                pct = float(match.group(1))
            except Exception:
                continue
            if pct > 100.0 + 1e-6:
                return True
    return False


def _trend_strings_have_mismatched_availability(*, home: str, away: str) -> bool:
    """Return True when one team has data and the other claims 'not available'."""
    home_s = (home or "").strip().lower()
    away_s = (away or "").strip().lower()

    missing_phrase = "not currently available"

    def has_data(s: str) -> bool:
        # Heuristic: trend strings with a record ("1-0-0 ATS" / "Over 1 times") contain digits.
        return any(ch.isdigit() for ch in s) and missing_phrase not in s

    def is_missing(s: str) -> bool:
        return missing_phrase in s

    # If both have data or both are missing, it's not mismatched.
    home_has = has_data(home_s)
    away_has = has_data(away_s)
    if home_has == away_has:
        return False

    # If exactly one is missing and the other has data, it's stale/mismatched.
    return (is_missing(home_s) and away_has) or (is_missing(away_s) and home_has)


def is_full_article_ready(content: Dict[str, Any]) -> bool:
    return bool(str(content.get("full_article") or "").strip())


def merge_preserving_full_article(
    *,
    existing: Optional[Dict[str, Any]],
    incoming: Dict[str, Any],
    force_refresh_core: bool = False,
) -> Dict[str, Any]:
    """
    Merge content, keeping a non-empty existing full_article when incoming is empty.
    
    Args:
        existing: Existing analysis content
        incoming: New analysis content to merge
        force_refresh_core: If True, completely replace core fields (ats_trends, totals_trends, etc.)
    """
    if force_refresh_core:
        # When forcing refresh, start with incoming and only preserve full_article if it exists
        merged: Dict[str, Any] = dict(incoming)
        existing_article = str((existing or {}).get("full_article") or "").strip()
        if existing_article:
            merged["full_article"] = existing_article
            # If we preserved a non-empty full article, ensure generation metadata matches.
            gen = merged.get("generation")
            gen_dict: Dict[str, Any] = dict(gen) if isinstance(gen, dict) else {}
            gen_dict["full_article_status"] = "ready"
            merged["generation"] = gen_dict
        return merged
    
    # Normal merge: preserve existing, update with incoming
    merged: Dict[str, Any] = dict(existing or {})
    merged.update(incoming)

    existing_article = str((existing or {}).get("full_article") or "").strip()
    incoming_article = str(incoming.get("full_article") or "").strip()
    if existing_article and not incoming_article:
        merged["full_article"] = existing_article
        # Core refreshes can overwrite generation metadata (e.g. status resets to "queued")
        # even when we preserved an already-generated full article. Keep status consistent.
        gen = merged.get("generation")
        gen_dict: Dict[str, Any] = dict(gen) if isinstance(gen, dict) else {}
        gen_dict["full_article_status"] = "ready"
        merged["generation"] = gen_dict

    return merged


@dataclass(frozen=True)
class GenerationMetadata:
    core_status: str
    full_article_status: str
    updated_at: str
    last_error: Optional[str] = None
    redaction_count: Optional[int] = None
    role_language_rewrite_count: Optional[int] = None

    def as_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "core_status": self.core_status,
            "full_article_status": self.full_article_status,
            "updated_at": self.updated_at,
        }
        if self.last_error:
            payload["last_error"] = self.last_error
        if self.redaction_count is not None:
            payload["redaction_count"] = self.redaction_count
        if self.role_language_rewrite_count is not None:
            payload["role_language_rewrite_count"] = self.role_language_rewrite_count
        return payload


def with_generation_metadata(
    content: Dict[str, Any],
    *,
    core_status: str,
    full_article_status: str,
    last_error: Optional[str] = None,
    redaction_count: Optional[int] = None,
    role_language_rewrite_count: Optional[int] = None,
) -> Dict[str, Any]:
    updated = dict(content)
    updated["generation"] = GenerationMetadata(
        core_status=core_status,
        full_article_status=full_article_status,
        updated_at=utc_now_iso(),
        last_error=last_error,
        redaction_count=redaction_count,
        role_language_rewrite_count=role_language_rewrite_count,
    ).as_dict()
    return updated


