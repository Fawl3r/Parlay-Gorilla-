"""
Team name alias map for Odds API -> API-Sports resolution.

Common mismatches: LA/NY abbreviations, punctuation variants.
resolve_team_id checks this before fuzzy normalization.
"""

from __future__ import annotations

from typing import Dict

# Odds API normalized key -> preferred lookup key (or API-Sports style name variant).
# Keys are normalized via teams_index_service.normalize_team_name.
TEAM_ALIASES: Dict[str, str] = {
    # LA / NY abbreviations and variants
    "la lakers": "los angeles lakers",
    "la clippers": "los angeles clippers",
    "ny knicks": "new york knicks",
    "ny jets": "new york jets",
    "ny giants": "new york giants",
    "ny yankees": "new york yankees",
    "ny mets": "new york mets",
    "ny rangers": "new york rangers",
    "ny islanders": "new york islanders",
    "la rams": "los angeles rams",
    "la chargers": "los angeles chargers",
    "la angels": "los angeles angels",
    "la kings": "los angeles kings",
    "la dodgers": "los angeles dodgers",
    # Punctuation / spelling variants
    "st louis cardinals": "st. louis cardinals",
    "st louis blues": "st. louis blues",
    "tampa bay buccaneers": "tampa bay buccaneers",
    "san francisco 49ers": "san francisco 49ers",
    "green bay packers": "green bay packers",
}


def get_team_alias(normalized_odds_name: str) -> str:
    """
    Return alias for normalized Odds API team name if one exists; otherwise return input.
    Used by resolve_team_id for first lookup before fuzzy match.
    """
    if not normalized_odds_name:
        return normalized_odds_name
    return TEAM_ALIASES.get(normalized_odds_name, normalized_odds_name)
