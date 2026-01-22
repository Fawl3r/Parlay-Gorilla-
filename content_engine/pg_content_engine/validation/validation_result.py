from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .validation_issue import ValidationIssue


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.issues

    def add_issue(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)

    def extend(self, issues: Iterable[ValidationIssue]) -> None:
        self.issues.extend(list(issues))

    def reasons(self) -> list[str]:
        return [issue.to_reason() for issue in self.issues]
