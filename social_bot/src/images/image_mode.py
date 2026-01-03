from __future__ import annotations

from enum import Enum


class ImageMode(str, Enum):
    quote_card = "quote_card"
    analysis_card = "analysis_card"
    persona = "persona"
    ui_tease = "ui_tease"
    generic = "generic"

    @staticmethod
    def from_value(value: str) -> "ImageMode":
        raw = (value or "").strip().lower()
        for mode in ImageMode:
            if mode.value == raw:
                return mode
        return ImageMode.generic


