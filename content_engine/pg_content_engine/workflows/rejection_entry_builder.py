from __future__ import annotations

from typing import Any

from ..models import ContentStatus


class RejectionEntryBuilder:
    def __init__(self, status: ContentStatus = ContentStatus.REJECTED) -> None:
        self._status = status

    def from_item_dict(self, item: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
        updated = dict(item)
        updated["status"] = self._status.value
        updated["rejection_reasons"] = list(reasons)
        return updated

    def from_raw(self, raw_item: Any, reasons: list[str]) -> dict[str, Any]:
        if isinstance(raw_item, dict):
            return self.from_item_dict(raw_item, reasons)
        return {
            "id": "unknown",
            "status": self._status.value,
            "rejection_reasons": list(reasons),
            "raw_item": repr(raw_item),
        }
