from __future__ import annotations

from ...models import XContentItem
from ...validation import ValidationIssue
from .x_rule import XRule


class XComplianceRule(XRule):
    def evaluate(self, item: XContentItem) -> list[ValidationIssue]:
        compliance = item.compliance
        if not (compliance.no_guarantees and compliance.no_hype and compliance.no_emojis):
            return [
                ValidationIssue(
                    code="compliance_flags",
                    message="Compliance flags must all be true.",
                    field="compliance",
                )
            ]
        return []
