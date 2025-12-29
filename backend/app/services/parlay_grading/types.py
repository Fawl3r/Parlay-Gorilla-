from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ParlayLegStatus(str, Enum):
    pending = "pending"
    hit = "hit"
    missed = "missed"
    push = "push"


@dataclass(frozen=True)
class ParsedLeg:
    """
    Normalized, grading-ready leg description.

    - market_type: h2h | spreads | totals
    - selection:
        - h2h: home | away | draw
        - spreads: home | away
        - totals: over | under
    - line: spread/total line (float) when applicable
    """

    market_type: str
    selection: str
    line: Optional[float]

    # Helpful for debugging/analytics:
    raw: Dict[str, Any]


