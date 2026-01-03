from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.models import PostedRecord, QueueItem


class QueueStoreError(RuntimeError):
    pass


class QueueStore:
    def __init__(self, queue_dir: Path) -> None:
        self._queue_dir = queue_dir
        self._queue_dir.mkdir(parents=True, exist_ok=True)
        self._outbox_path = self._queue_dir / "outbox.json"
        self._posted_path = self._queue_dir / "posted.json"
        self._ensure_files()

    def load_outbox(self) -> List[Dict[str, Any]]:
        return self._read_list(self._outbox_path)

    def save_outbox(self, items: List[Dict[str, Any]]) -> None:
        self._write_list_atomic(self._outbox_path, items)

    def append_outbox(self, items: List[Dict[str, Any]]) -> None:
        current = self.load_outbox()
        current.extend(items)
        self.save_outbox(current)

    def remove_outbox_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        current = self.load_outbox()
        kept: List[Dict[str, Any]] = []
        removed: Optional[Dict[str, Any]] = None
        for item in current:
            if str(item.get("id")) == item_id and removed is None:
                removed = item
                continue
            kept.append(item)
        if removed is not None:
            self.save_outbox(kept)
        return removed

    def load_posted(self) -> List[Dict[str, Any]]:
        return self._read_list(self._posted_path)

    def append_posted(self, record: PostedRecord) -> None:
        current = self.load_posted()
        current.append(record.to_dict())
        self._write_list_atomic(self._posted_path, current)

    def hydrate_outbox_items(self) -> List[QueueItem]:
        items: List[QueueItem] = []
        for raw in self.load_outbox():
            items.append(
                QueueItem(
                    id=str(raw.get("id") or ""),
                    type=str(raw.get("type") or "single"),
                    text=(str(raw.get("text")) if raw.get("text") is not None else None),
                    tweets=[str(x) for x in (raw.get("tweets") or [])] if raw.get("tweets") else None,
                    topic=(str(raw.get("topic")) if raw.get("topic") is not None else None),
                    pillar_id=str(raw.get("pillar_id") or ""),
                    template_id=str(raw.get("template_id") or ""),
                    score=float(raw.get("score") or 0.0),
                    recommended_tier=str(raw.get("recommended_tier") or ""),
                    created_at=str(raw.get("created_at") or ""),
                )
            )
        return items

    def _ensure_files(self) -> None:
        for path in [self._outbox_path, self._posted_path]:
            if not path.exists():
                path.write_text("[]", encoding="utf-8")

    def _read_list(self, path: Path) -> List[Dict[str, Any]]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8") or "[]")
            if isinstance(raw, list):
                return [x for x in raw if isinstance(x, dict)]
            return []
        except Exception as exc:
            raise QueueStoreError(f"Failed reading JSON: {path}") from exc

    def _write_list_atomic(self, path: Path, value: List[Any]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        data = json.dumps(value, ensure_ascii=False, indent=2)
        try:
            tmp.write_text(data, encoding="utf-8")
            os.replace(tmp, path)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except Exception:
                    pass


