from __future__ import annotations

from typing import Any

from ..models import ContentStatus


class StatusUpdater:
    def with_status(self, item_dict: dict[str, Any], status: ContentStatus) -> dict[str, Any]:
        updated = dict(item_dict)
        updated["status"] = status.value
        return updated
