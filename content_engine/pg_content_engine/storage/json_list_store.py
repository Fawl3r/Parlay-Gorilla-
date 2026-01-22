from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .json_file_gateway import JsonFileGateway


@dataclass
class JsonListStore:
    path: Path
    gateway: JsonFileGateway

    def load(self) -> list[Any]:
        return self.gateway.read_list(self.path)

    def save(self, items: list[Any]) -> None:
        self.gateway.write_list(self.path, items)

    def append(self, items: list[Any]) -> None:
        existing = self.load()
        existing.extend(items)
        self.save(existing)
