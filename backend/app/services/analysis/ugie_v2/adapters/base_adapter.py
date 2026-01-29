"""Base adapter interface for sport-specific normalization of matchup_data."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NormalizedUgieInputs:
    """
    Normalized inputs for UGIE pillars from matchup_data.
    Adapters populate these when data is present; missing list records gaps.
    """

    availability: Optional[Dict[str, Any]] = None
    efficiency: Optional[Dict[str, Any]] = None
    matchup: Optional[Dict[str, Any]] = None
    missing: List[str] = field(default_factory=list)

    def merge_missing(self, other: List[str]) -> None:
        """Add items from other to missing without duplicates."""
        for x in other:
            if x not in self.missing:
                self.missing.append(x)


class BaseUgieAdapter(ABC):
    """
    Translate-only: normalize matchup_data into availability, efficiency,
    and matchup signals. Use existing dict paths (legacy + v2).
    """

    @abstractmethod
    def normalize(self, matchup_data: Dict[str, Any], game: Any = None) -> NormalizedUgieInputs:
        """
        Produce normalized inputs for UGIE. Add to .missing when data is absent.
        game is optional for sport/team context.
        """
        pass
