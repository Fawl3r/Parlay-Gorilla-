from __future__ import annotations

from abc import ABC, abstractmethod

from ...models import VideoContentItem
from ...validation import ValidationIssue


class VideoRule(ABC):
    @abstractmethod
    def evaluate(self, item: VideoContentItem) -> list[ValidationIssue]:
        raise NotImplementedError
