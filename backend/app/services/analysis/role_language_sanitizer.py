"""Post-generation neutralizer for pronouns and implied single-player phrasing.

Removes lingering player-centric language (e.g. "his ability", "the signal-caller")
so analysis narratives stay role-first and team/unit-centric. Applied only to
analysis body text; markdown headings are left unchanged.
"""

from __future__ import annotations

import re
from typing import Tuple


# Phrase replacements (applied in order; more specific first).
_PHRASE_REPLACEMENTS: list[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bhis ability to\b", re.IGNORECASE), "the offense's ability to"),
    (re.compile(r"\bhis performance\b", re.IGNORECASE), "the unit's performance"),
    (re.compile(r"\bhis role\b", re.IGNORECASE), "the unit's role"),
    (re.compile(r"\bhis leadership\b", re.IGNORECASE), "offensive leadership"),
    (re.compile(r"\bher ability to\b", re.IGNORECASE), "the offense's ability to"),
    (re.compile(r"\bher performance\b", re.IGNORECASE), "the unit's performance"),
    (re.compile(r"\bthe quarterback's ability\b", re.IGNORECASE), "quarterback play"),
    (re.compile(r"\bthe quarterback's performance\b", re.IGNORECASE), "quarterback performance"),
    (re.compile(r"\bthe quarterback's leadership\b", re.IGNORECASE), "offensive leadership"),
    (re.compile(r"\bthe signal-caller's ability\b", re.IGNORECASE), "quarterback play"),
    (re.compile(r"\bthe signal-caller's leadership\b", re.IGNORECASE), "offensive leadership"),
    (re.compile(r"\bthe signal-caller\b", re.IGNORECASE), "the quarterback"),
    (re.compile(r"\bthe star player\b", re.IGNORECASE), "key playmakers"),
]

# Standalone pronoun tokens (word boundary; applied after phrase pass).
_PRONOUN_REPLACEMENTS: list[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bhis\b", re.IGNORECASE), "the unit's"),
    (re.compile(r"\bhim\b", re.IGNORECASE), "the unit"),
    (re.compile(r"\bhe\b", re.IGNORECASE), "the unit"),
    (re.compile(r"\bher\b", re.IGNORECASE), "the unit's"),
    (re.compile(r"\bshe\b", re.IGNORECASE), "the unit"),
]


def _is_heading_line(line: str) -> bool:
    """Return True if the line is a markdown heading (starts with # after strip)."""
    return line.strip().startswith("#")


def _apply_replacements_to_line(line: str) -> Tuple[str, int]:
    """Apply phrase and pronoun replacements to one line; return (new_line, count)."""
    count = 0
    text = line
    for pattern, repl in _PHRASE_REPLACEMENTS:
        new_text, n = pattern.subn(repl, text)
        if n:
            count += n
            text = new_text
    for pattern, repl in _PRONOUN_REPLACEMENTS:
        new_text, n = pattern.subn(repl, text)
        if n:
            count += n
            text = new_text
    return (text, count)


class RoleLanguageSanitizer:
    """
    Neutralize pronouns and implied single-player phrasing in analysis text.

    Single responsibility: regex-based replacement so that narratives are
    role-first and team/unit-centric. Does not touch markdown headings.
    Never introduces player names.
    """

    def sanitize(self, text: str) -> Tuple[str, int]:
        """
        Return (sanitized_text, replacement_count). Only non-heading lines
        are modified; headings are preserved unchanged.
        """
        if not text or not isinstance(text, str):
            return (str(text or ""), 0)

        lines = text.split("\n")
        out: list[str] = []
        total_count = 0
        for line in lines:
            if _is_heading_line(line):
                out.append(line)
                continue
            new_line, count = _apply_replacements_to_line(line)
            out.append(new_line)
            total_count += count
        return ("\n".join(out), total_count)
