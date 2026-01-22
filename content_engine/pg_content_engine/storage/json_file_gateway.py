from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonFileGateway:
    def read_list(self, path: Path) -> list[Any]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON array at {path}.")
        return data

    def write_list(self, path: Path, items: list[Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(items, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
