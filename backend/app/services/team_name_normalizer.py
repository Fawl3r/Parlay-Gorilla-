"""Team name normalization for cross-provider matching.

We ingest teams from multiple sources (The Odds API, ESPN, SportsRadar). Names
can differ slightly (punctuation, '&' vs 'and', prefixes like 'FC', etc.). This
utility creates a stable, conservative normalization used for dedupe keys.

Important: This should NOT be overly aggressive (e.g., removing 'United'/'City')
because that can incorrectly merge distinct teams.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TeamNameNormalizer:
    _STRIP_EDGE_TOKENS = {
        # Common soccer prefixes/suffixes
        "fc",
        "cf",
        "sc",
        "afc",
        "ud",
        "rcd",
        "ac",
        "as",
        "ssc",
        "ca",
    }

    def normalize(self, name: str) -> str:
        s = str(name or "").strip().lower()
        if not s:
            return ""

        # Normalize common punctuation variants.
        s = s.replace("&", " and ")

        # Replace all punctuation with spaces (keep letters/digits/underscore).
        s = re.sub(r"[^\w\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()

        tokens = s.split()
        # Strip known generic tokens from both ends only.
        while tokens and tokens[0] in self._STRIP_EDGE_TOKENS:
            tokens.pop(0)
        while tokens and tokens[-1] in self._STRIP_EDGE_TOKENS:
            tokens.pop()

        return " ".join(tokens).strip()



