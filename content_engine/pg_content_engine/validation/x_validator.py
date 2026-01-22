from __future__ import annotations

from ..models import XContentItem
from ..rules.x.x_rule import XRule
from .validation_result import ValidationResult


class XValidator:
    def __init__(self, rules: list[XRule]) -> None:
        self._rules = rules

    def validate(self, item: XContentItem) -> ValidationResult:
        result = ValidationResult()
        for rule in self._rules:
            result.extend(rule.evaluate(item))
        return result
