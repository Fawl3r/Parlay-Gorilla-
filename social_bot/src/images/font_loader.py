from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import ImageFont


@dataclass(frozen=True)
class LoadedFonts:
    headline: ImageFont.ImageFont
    subtext: ImageFont.ImageFont


class FontLoader:
    def load(self, *, preferred_path: Optional[Path], headline_size: int, subtext_size: int) -> LoadedFonts:
        headline = self._load_one(preferred_path, headline_size) or self._load_fallback(headline_size)
        subtext = self._load_one(preferred_path, subtext_size) or self._load_fallback(subtext_size)
        return LoadedFonts(headline=headline, subtext=subtext)

    def _load_one(self, path: Optional[Path], size: int) -> Optional[ImageFont.ImageFont]:
        if not path:
            return None
        try:
            if not path.exists():
                return None
            return ImageFont.truetype(str(path), size=size)
        except Exception:
            return None

    def _load_fallback(self, size: int) -> ImageFont.ImageFont:
        for name in ["arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]:
            try:
                return ImageFont.truetype(name, size=size)
            except Exception:
                continue
        return ImageFont.load_default()


