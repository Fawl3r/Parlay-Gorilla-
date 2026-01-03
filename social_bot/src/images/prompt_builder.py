from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.images.character_spec import CharacterSpec
from src.images.image_mode import ImageMode


_GLOBAL_SAFETY = "no logos, no team logos, no team names, no brand names, no sportsbook names, no text, no words, no people faces"


@dataclass(frozen=True)
class ImagePrompt:
    prompt: str


class ImagePromptBuilder:
    def __init__(self, *, character: Optional[CharacterSpec] = None) -> None:
        self._character = character

    def build(self, *, mode: ImageMode, strictness: int = 0) -> ImagePrompt:
        extra = ""
        if strictness > 0:
            extra = "absolutely no letters, no numbers, no signage, no uniforms, no emblems, no badges, "

        if mode == ImageMode.analysis_card:
            return ImagePrompt(
                prompt=(
                    "Dark sports analytics dashboard style background, abstract charts and data glow, "
                    "neon green highlights, futuristic, clean, cinematic lighting, shallow depth of field, "
                    f"{extra}{_GLOBAL_SAFETY}"
                )
            )

        if mode == ImageMode.persona:
            character = self._character.prompt_anchors() if self._character else "Stylized realistic western lowland gorilla, cinematic, neon green accents"
            return ImagePrompt(
                prompt=(
                    f"{character}, "
                    "dramatic rim lighting, dark background, neon green highlights, powerful posture, "
                    "professional sports photography style, high contrast, "
                    f"{extra}{_GLOBAL_SAFETY}"
                )
            )

        if mode == ImageMode.ui_tease:
            return ImagePrompt(
                prompt=(
                    "Dark-mode sports analytics app UI tease background, blurred dashboard cards and panels, "
                    "abstract charts glow, neon green accents, futuristic, premium, cinematic, "
                    "no readable text, no letters, "
                    f"{extra}{_GLOBAL_SAFETY}"
                )
            )

        if mode == ImageMode.quote_card:
            return ImagePrompt(
                prompt=(
                    "Premium minimal dark gradient background with subtle stadium lighting bokeh, "
                    "neon green accents, high contrast, cinematic, "
                    f"{extra}{_GLOBAL_SAFETY}"
                )
            )

        return ImagePrompt(
            prompt=(
                "Ultra-realistic cinematic sports stadium at night, dramatic lighting, dark tones, neon green accents, "
                "shallow depth of field, high contrast, "
                f"{extra}{_GLOBAL_SAFETY}"
            )
        )


