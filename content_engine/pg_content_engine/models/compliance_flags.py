from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ComplianceFlags:
    no_guarantees: bool
    no_hype: bool
    no_emojis: bool

    @classmethod
    def from_dict(cls, data: Any) -> "ComplianceFlags":
        if not isinstance(data, dict):
            raise ValueError("Compliance must be an object.")
        no_guarantees = data.get("no_guarantees")
        no_hype = data.get("no_hype")
        no_emojis = data.get("no_emojis")
        if not all(isinstance(value, bool) for value in [no_guarantees, no_hype, no_emojis]):
            raise ValueError("Compliance flags must all be boolean values.")
        return cls(
            no_guarantees=no_guarantees,
            no_hype=no_hype,
            no_emojis=no_emojis,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "no_guarantees": self.no_guarantees,
            "no_hype": self.no_hype,
            "no_emojis": self.no_emojis,
        }
