from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ItemValidationOutcome:
    content_id: str
    is_valid: bool
    reasons: list[str]

    def summary_line(self) -> str:
        reason_text = "; ".join(self.reasons) if self.reasons else "No issues."
        status = "valid" if self.is_valid else "invalid"
        return f"{self.content_id}: {status} - {reason_text}"
