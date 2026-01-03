from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_ts() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class LoggingManager:
    def __init__(self, logs_dir: Path, level: str = "INFO") -> None:
        self._logs_dir = logs_dir
        self._logs_dir.mkdir(parents=True, exist_ok=True)
        self._level = level

    def build_logger(self) -> logging.Logger:
        logger = logging.getLogger("social_bot")
        if logger.handlers:
            return logger

        logger.setLevel(self._level.upper())
        logger.propagate = False

        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        file_handler = logging.FileHandler(self._logs_dir / "bot.log", encoding="utf-8")
        file_handler.setFormatter(fmt)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(fmt)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        return logger


class AuditLogger:
    def __init__(self, logs_dir: Path) -> None:
        self._path = logs_dir / "audit.jsonl"
        logs_dir.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("", encoding="utf-8")

    def write(self, event: str, payload: Dict[str, Any], *, ts: Optional[str] = None) -> None:
        record = {"ts": ts or _utc_ts(), "event": event, **payload}
        line = json.dumps(record, ensure_ascii=False)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


