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
from typing import Optional


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

    def normalize(self, name: str, sport: Optional[str] = None) -> str:
        """
        Normalize team name for cross-provider matching.
        
        Args:
            name: Team name to normalize
            sport: Optional sport code (e.g., "NFL", "SOCCER") to apply sport-specific rules
        
        Returns:
            Normalized team name
        """
        s = str(name or "").strip().lower()
        if not s:
            return ""

        # Special handling: If the name is exactly "AFC" or "NFC" (standalone), 
        # don't normalize it - these are placeholder team names that should be filtered out
        # at a higher level, but if they somehow get here, preserve them for detection
        if s in ("afc", "nfc"):
            return s

        # Normalize common punctuation variants.
        s = s.replace("&", " and ")

        # Replace all punctuation with spaces (keep letters/digits/underscore).
        s = re.sub(r"[^\w\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()

        tokens = s.split()
        
        # For NFL, don't strip "AFC" or "NFC" as they might be part of team names
        # (though standalone "AFC"/"NFC" should be filtered out before normalization)
        strip_tokens = self._STRIP_EDGE_TOKENS.copy()
        if sport and sport.upper() in ("NFL", "AMERICANFOOTBALL_NFL"):
            # For NFL, only strip "afc" if it's part of a longer name (like "AFC Ajax" doesn't exist in NFL)
            # But we want to preserve "AFC" and "NFC" if they're standalone
            # Actually, if it's standalone, we already handled it above
            # If it's part of a name, we should strip it (but NFL teams don't have "AFC" in their names)
            # So for NFL, we can be more conservative and not strip "afc" at all
            strip_tokens = strip_tokens - {"afc", "nfc"}
        
        # Strip known generic tokens from both ends only.
        while tokens and tokens[0] in strip_tokens:
            tokens.pop(0)
        while tokens and tokens[-1] in strip_tokens:
            tokens.pop()

        return " ".join(tokens).strip()



