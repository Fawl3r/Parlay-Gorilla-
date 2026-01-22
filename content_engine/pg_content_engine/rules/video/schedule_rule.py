from __future__ import annotations

from ...models import VideoContentItem
from ...validation import ValidationIssue
from .video_rule import VideoRule


class VideoScheduleRule(VideoRule):
    _ALLOWED_EXPIRATIONS = {24, 48, 72}

    def evaluate(self, item: VideoContentItem) -> list[ValidationIssue]:
        schedule = item.schedule
        if schedule.evergreen and schedule.expiration_hours is not None:
            return [
                ValidationIssue(
                    code="schedule_invalid",
                    message="Evergreen posts must not have expiration_hours.",
                    field="schedule",
                )
            ]
        if not schedule.evergreen and schedule.expiration_hours not in self._ALLOWED_EXPIRATIONS:
            return [
                ValidationIssue(
                    code="schedule_invalid",
                    message="Non-evergreen posts must set expiration_hours to 24, 48, or 72.",
                    field="schedule",
                )
            ]
        return []
