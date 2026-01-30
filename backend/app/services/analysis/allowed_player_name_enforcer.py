"""
Enforcer: redact player-name patterns unless the name is in the allowlist.

Used after full-article generation when roster allowlist is available.
When allowlist is empty, all player-name patterns are redacted (same as sanitizer).
"""

from __future__ import annotations

import re
from typing import Collection, Optional, Set


def _normalize_for_allowlist(name: str) -> str:
    """Normalize name for allowlist lookup (trim, title-case)."""
    if not name or not isinstance(name, str):
        return ""
    return " ".join(name.split()).strip()


def _allowlist_set(allowed: Optional[Collection[str]]) -> Set[str]:
    """Return set of normalized allowed names (case-insensitive for lookup)."""
    if not allowed:
        return set()
    return {" ".join(_normalize_for_allowlist(n).split()).lower() for n in allowed if n}


def _name_in_allowlist(name: str, allowlist: Set[str]) -> bool:
    """Check if name (from match) is in allowlist (normalize spacing and case)."""
    if not name or not allowlist:
        return False
    normalized = " ".join(name.split()).strip().lower()
    return normalized in allowlist


# Same patterns as ArticlePlayerReferenceSanitizer
_LED_BY_NAME = re.compile(
    r"\bled by ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b",
    re.IGNORECASE,
)
_REPLACEMENT_LED_BY = "led by its core playmakers"

_QB_NAME = re.compile(
    r"\b(quarterback|QB)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b",
    re.IGNORECASE,
)
_REPLACEMENT_QB = r"\1"

_RB_WR_NAME = re.compile(
    r"\b(running back|RB|wide receiver|WR|tight end|TE)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b",
    re.IGNORECASE,
)
_REPLACEMENT_RB_WR = r"\1"

_STAR_NAME = re.compile(
    r"\b(star|leading scorer|go-to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b",
    re.IGNORECASE,
)
_REPLACEMENT_STAR = r"\1"

_NAME_WILL = re.compile(
    r"\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+will\b",
)
_REPLACEMENT_NAME_WILL = "The unit will"


class AllowedPlayerNameEnforcer:
    """
    Redact player-name references in text unless the name is in the allowlist.

    Single responsibility: apply the same substitutions as ArticlePlayerReferenceSanitizer,
    but only when the matched name is NOT in the allowed set. Preserves markdown headings.
    """

    def enforce(
        self,
        text: str,
        allowed_player_names: Optional[Collection[str]] = None,
    ) -> str:
        """
        Return text with player-name patterns redacted unless the name is in allowed_player_names.
        If allowed_player_names is None or empty, redact all such patterns.
        """
        if not text or not isinstance(text, str):
            return str(text or "")

        allowlist = _allowlist_set(allowed_player_names)

        def _repl_led_by(m: re.Match) -> str:
            name = (m.group(1) or "").strip()
            if name and name.lower() in allowlist:
                return m.group(0)
            return _REPLACEMENT_LED_BY

        def _repl_qb(m: re.Match) -> str:
            name = (m.group(2) or "").strip()
            if name and name.lower() in allowlist:
                return m.group(0)
            return _REPLACEMENT_QB if m.lastindex and m.lastindex >= 1 else m.group(1)

        def _repl_qb_grp(m: re.Match) -> str:
            role = (m.group(1) or "").strip()
            name = (m.group(2) or "").strip()
            if name and name.lower() in allowlist:
                return m.group(0)
            return role

        def _repl_rb_wr(m: re.Match) -> str:
            name = (m.group(2) or "").strip()
            if _name_in_allowlist(name, allowlist):
                return m.group(0)
            return (m.group(1) or "").strip()

        def _repl_star(m: re.Match) -> str:
            name = (m.group(2) or "").strip()
            if _name_in_allowlist(name, allowlist):
                return m.group(0)
            return (m.group(1) or "").strip()

        def _repl_name_will(m: re.Match) -> str:
            name = (m.group(1) or "").strip()
            if _name_in_allowlist(name, allowlist):
                return m.group(0)
            return _REPLACEMENT_NAME_WILL

        cleaned = text
        cleaned = _LED_BY_NAME.sub(_repl_led_by, cleaned)
        cleaned = _QB_NAME.sub(_repl_qb_grp, cleaned)
        cleaned = _RB_WR_NAME.sub(_repl_rb_wr, cleaned)
        cleaned = _STAR_NAME.sub(_repl_star, cleaned)
        cleaned = _NAME_WILL.sub(_repl_name_will, cleaned)
        return cleaned
