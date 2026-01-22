from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    field: str | None = None

    def to_reason(self) -> str:
        if self.field:
            return f"{self.field}: {self.message}"
        return self.message
