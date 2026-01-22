from __future__ import annotations

from dataclasses import dataclass

from .item_validation_outcome import ItemValidationOutcome


@dataclass(frozen=True)
class QueueValidationReport:
    total: int
    valid_count: int
    invalid_count: int
    outcomes: list[ItemValidationOutcome]

    def summary_lines(self) -> list[str]:
        lines = [
            f"Total: {self.total}",
            f"Valid: {self.valid_count}",
            f"Invalid: {self.invalid_count}",
        ]
        for outcome in self.outcomes:
            if not outcome.is_valid:
                lines.append(outcome.summary_line())
        return lines
