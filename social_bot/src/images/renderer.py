from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw

from src.images.font_loader import FontLoader


@dataclass(frozen=True)
class RenderSpec:
    size: Tuple[int, int]
    margin_px: int
    headline_font_px: int
    subtext_font_px: int
    watermark_width_px: int
    watermark_opacity: int  # 0..255


class ImageRenderer:
    def __init__(self, *, font_loader: FontLoader) -> None:
        self._font_loader = font_loader

    def render(
        self,
        *,
        background: Image.Image,
        headline: str,
        subtext: Optional[str],
        output_size: Tuple[int, int],
        logo_path: Path,
        font_path: Optional[Path],
    ) -> Image.Image:
        base = self._prepare_base(background, output_size)
        draw = ImageDraw.Draw(base)

        spec = self._build_spec(output_size)
        fonts = self._font_loader.load(preferred_path=font_path, headline_size=spec.headline_font_px, subtext_size=spec.subtext_font_px)

        headline_lines = self._wrap(draw, headline, fonts.headline, max_width=output_size[0] - 2 * spec.margin_px)
        subtext_lines = self._wrap(draw, subtext or "", fonts.subtext, max_width=output_size[0] - 2 * spec.margin_px) if subtext else []

        self._draw_text_block(
            draw,
            headline_lines=headline_lines,
            subtext_lines=subtext_lines,
            fonts=(fonts.headline, fonts.subtext),
            output_size=output_size,
            margin_px=spec.margin_px,
        )
        self._apply_watermark(base, logo_path=logo_path, width_px=spec.watermark_width_px, opacity=spec.watermark_opacity, margin_px=spec.margin_px)
        return base

    def _build_spec(self, size: Tuple[int, int]) -> RenderSpec:
        w, _ = size
        margin = max(56, int(w * 0.07))
        return RenderSpec(
            size=size,
            margin_px=margin,
            headline_font_px=max(54, int(w * 0.07)),
            subtext_font_px=max(30, int(w * 0.04)),
            watermark_width_px=max(160, int(w * 0.18)),
            watermark_opacity=140,
        )

    def _prepare_base(self, image: Image.Image, output_size: Tuple[int, int]) -> Image.Image:
        base = image.convert("RGBA")
        if base.size != output_size:
            base = base.resize(output_size, resample=Image.Resampling.LANCZOS)
        return base

    def _wrap(self, draw: ImageDraw.ImageDraw, text: str, font, *, max_width: int) -> List[str]:
        words = [w for w in (text or "").split() if w]
        if not words:
            return []
        lines: List[str] = []
        current: List[str] = []
        for word in words:
            trial = " ".join(current + [word])
            if self._text_width(draw, trial, font) <= max_width or not current:
                current.append(word)
                continue
            lines.append(" ".join(current))
            current = [word]
        if current:
            lines.append(" ".join(current))
        return lines[:6]

    def _text_width(self, draw: ImageDraw.ImageDraw, text: str, font) -> int:
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=4)
        return int(bbox[2] - bbox[0])

    def _draw_text_block(
        self,
        draw: ImageDraw.ImageDraw,
        *,
        headline_lines: List[str],
        subtext_lines: List[str],
        fonts: Tuple,
        output_size: Tuple[int, int],
        margin_px: int,
    ) -> None:
        if not headline_lines:
            return

        headline_font, subtext_font = fonts
        max_width = output_size[0] - 2 * margin_px
        line_gap = 10
        head_h = self._block_height(draw, headline_lines, headline_font, gap=line_gap)
        sub_h = self._block_height(draw, subtext_lines, subtext_font, gap=6) if subtext_lines else 0
        total_h = head_h + (18 if subtext_lines else 0) + sub_h

        x0 = margin_px
        y0 = max(margin_px, int(output_size[1] * 0.16))
        x1 = x0 + max_width
        y1 = min(output_size[1] - margin_px, y0 + total_h + 44)

        draw.rounded_rectangle((x0 - 18, y0 - 18, x1 + 18, y1), radius=28, fill=(0, 0, 0, 170))

        y = y0
        for line in headline_lines:
            draw.text((x0, y), line, font=headline_font, fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0, 220))
            y += self._line_height(draw, line, headline_font) + line_gap

        if subtext_lines:
            y += 8
            for line in subtext_lines[:2]:
                draw.text((x0, y), line, font=subtext_font, fill=(210, 255, 225, 255), stroke_width=3, stroke_fill=(0, 0, 0, 200))
                y += self._line_height(draw, line, subtext_font) + 6

    def _line_height(self, draw: ImageDraw.ImageDraw, text: str, font) -> int:
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=4)
        return int(bbox[3] - bbox[1])

    def _block_height(self, draw: ImageDraw.ImageDraw, lines: List[str], font, *, gap: int) -> int:
        if not lines:
            return 0
        total = 0
        for idx, line in enumerate(lines):
            total += self._line_height(draw, line, font)
            if idx < len(lines) - 1:
                total += gap
        return total

    def _apply_watermark(self, base: Image.Image, *, logo_path: Path, width_px: int, opacity: int, margin_px: int) -> None:
        if not logo_path.exists():
            return
        try:
            logo = Image.open(logo_path).convert("RGBA")
        except Exception:
            return

        ratio = width_px / float(max(1, logo.size[0]))
        height = max(1, int(logo.size[1] * ratio))
        logo = logo.resize((width_px, height), resample=Image.Resampling.LANCZOS)

        if opacity < 255:
            r, g, b, a = logo.split()
            a = a.point(lambda px: int(px * (opacity / 255.0)))
            logo = Image.merge("RGBA", (r, g, b, a))

        x = base.size[0] - margin_px - logo.size[0]
        y = base.size[1] - margin_px - logo.size[1]
        base.alpha_composite(logo, (max(margin_px, x), max(margin_px, y)))


