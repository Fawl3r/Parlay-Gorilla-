"""Next-action templates for alert payloads."""

from typing import Dict, List, Optional

NEXT_ACTIONS: Dict[str, str] = {
    "load_games": "Load games via refresh job or API-Sports.",
    "different_sport_or_week": "Try a different sport or week.",
    "wait_or_different_sport": "Wait for schedule or try a different sport.",
    "sync_odds_or_retry": "Sync odds or retry in a few moments.",
    "different_sport_or_later": "Try a different sport or again later.",
    "circuit_breaker_open": "Wait for circuit breaker cooldown.",
    "yellow_limit": "APISports quota in yellow zone; use ESPN fallback or wait.",
    "red_limit": "APISports quota exhausted for this sport today.",
}


def get_next_actions(next_action_hint: Optional[str], extra: Optional[List[str]] = None) -> List[str]:
    """Return list of next-action strings for an alert."""
    actions: List[str] = []
    if next_action_hint:
        actions.append(NEXT_ACTIONS.get(next_action_hint, next_action_hint))
    if extra:
        actions.extend(extra)
    return actions
