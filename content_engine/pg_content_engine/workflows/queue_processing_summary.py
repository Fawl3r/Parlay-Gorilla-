from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QueueProcessingSummary:
    total: int
    approved_count: int
    rejected_count: int
    error_count: int

    def summary_lines(self) -> list[str]:
        return [
            f"Total processed: {self.total}",
            f"Approved: {self.approved_count}",
            f"Rejected: {self.rejected_count}",
            f"Errors: {self.error_count}",
        ]
