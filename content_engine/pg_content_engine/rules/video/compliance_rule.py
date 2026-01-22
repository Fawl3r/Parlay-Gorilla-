from __future__ import annotations

from ...models import VideoContentItem
from ...validation import ValidationIssue
from .video_rule import VideoRule


class VideoComplianceRule(VideoRule):
    def evaluate(self, item: VideoContentItem) -> list[ValidationIssue]:
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
