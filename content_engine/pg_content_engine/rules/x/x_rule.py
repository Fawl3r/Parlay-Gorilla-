from __future__ import annotations

from abc import ABC, abstractmethod

from ...models import XContentItem
from ...validation import ValidationIssue


class XRule(ABC):
    @abstractmethod
    def evaluate(self, item: XContentItem) -> list[ValidationIssue]:
        raise NotImplementedError
