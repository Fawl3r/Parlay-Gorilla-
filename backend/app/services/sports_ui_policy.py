"""UI-oriented policy for sports visibility and availability labels.

This keeps the backend "source of truth" for which sports should be shown on
selection UIs (e.g., `/sports`) and how unavailable sports should be labeled.

It does NOT remove underlying support for a sport elsewhere in the system
(e.g., stored games, historical analyses). It only affects the sports listing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet


@dataclass(frozen=True)
class SportsUiPolicy:
    hidden_slugs: FrozenSet[str]
    coming_soon_slugs: FrozenSet[str]

    @staticmethod
    def default() -> "SportsUiPolicy":
        # Hide Champions League from UI lists.
        hidden = frozenset({"ucl"})
        # Expose combat sports as "Coming Soon" until the full UX is ready.
        coming_soon = frozenset({"ufc", "boxing"})
        return SportsUiPolicy(hidden_slugs=hidden, coming_soon_slugs=coming_soon)

    def should_hide(self, slug: str) -> bool:
        return str(slug or "").lower().strip() in self.hidden_slugs

    def apply_overrides(self, item: Dict[str, Any]) -> Dict[str, Any]:
        slug = str(item.get("slug") or "").lower().strip()
        if slug in self.coming_soon_slugs:
            # Force non-clickable in the UI and provide a clear label.
            item["in_season"] = False
            item["status_label"] = "Coming Soon"
        return item





