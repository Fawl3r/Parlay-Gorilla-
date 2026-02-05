from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GameStatusNormalizer:
    """
    Normalize upstream game status strings into a small canonical set.

    Why:
    - ESPN scoreboard often returns `status.type.name` like `STATUS_SCHEDULED`.
    - Odds API ingestion uses `scheduled`.
    - Parlay candidate generation historically filtered strictly on `scheduled`,
      which can exclude ESPN-sourced (or promoted) games even when odds exist.
    """

    # Canonical statuses used by our `Game` model queries.
    SCHEDULED: str = "scheduled"
    IN_PROGRESS: str = "in_progress"
    FINAL: str = "final"

    @classmethod
    def normalize(cls, raw: Optional[str]) -> str:
        value = (raw or "").strip()
        if not value:
            return cls.SCHEDULED

        lowered = value.lower().strip()

        # ESPN often uses `STATUS_*` (e.g., STATUS_SCHEDULED / STATUS_FINAL).
        if lowered.startswith("status_"):
            lowered = lowered[len("status_") :].strip()

        if lowered in {"scheduled", "pre", "preview", "created"}:
            return cls.SCHEDULED

        if lowered in {"inprogress", "in_progress", "live", "halftime", "half"}:
            return cls.IN_PROGRESS

        # FINAL variants across providers: FINAL, Final, FT, Finished, Game Over, Ended, etc.
        if lowered in {
            "final", "finished", "closed", "complete", "post",
            "ft", "game over", "ended", "full time", "fulltime",
        }:
            return cls.FINAL

        # Suspended / postponed / no contest / cancelled: do NOT treat as FINAL; settlement must not run until truly final.
        # Normalize all provider variants so settlement and void logic are consistent.
        if lowered in {"suspended", "suspend", "susp"}:
            return "suspended"
        if lowered in {"postponed", "postpone", "ppd", "delayed"}:
            return "postponed"
        if lowered in {"abandoned"}:
            return "postponed"  # treat like postponed for settlement (do not auto-void)
        if lowered in {"no contest", "no_contest", "noconstant", "cancelled", "canceled"}:
            return "no_contest"

        # Unknown: keep original lowered value to avoid hiding new upstream states.
        return lowered


