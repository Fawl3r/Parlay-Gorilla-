from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from random import Random
from typing import Optional, Tuple

from src.images.character_spec import CharacterSpec
from src.images.headline_extractor import HeadlineExtractor
from src.images.mode_decider import ImageModeDecider
from src.images.prompt_builder import ImagePromptBuilder
from src.images.providers.base import BackgroundRequest, BackgroundImageProvider, ProviderError
from src.images.renderer import ImageRenderer
from src.images.validators.base import VisionValidator
from src.settings import ImagesSettings


@dataclass(frozen=True)
class ImageAttachment:
    image_mode: str
    image_path: str


class ImagePipeline:
    def __init__(
        self,
        *,
        project_root: Path,
        settings: ImagesSettings,
        provider: BackgroundImageProvider,
        mode_decider: ImageModeDecider,
        prompt_builder: ImagePromptBuilder,
        headline_extractor: HeadlineExtractor,
        renderer: ImageRenderer,
        character: Optional[CharacterSpec] = None,
        validator: Optional[VisionValidator] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._project_root = project_root
        self._settings = settings
        self._provider = provider
        self._mode_decider = mode_decider
        self._prompt_builder = prompt_builder
        self._headline_extractor = headline_extractor
        self._renderer = renderer
        self._character = character
        self._validator = validator
        self._logger = logger or logging.getLogger("social_bot")

    def maybe_generate(
        self,
        *,
        post_id: str,
        post_text: str,
        pillar_id: str,
        template_id: str,
        rng: Optional[Random] = None,
        now: Optional[datetime] = None,
    ) -> Optional[ImageAttachment]:
        if not self._settings.enabled:
            return None

        rng = rng or Random()
        now = now or datetime.now(timezone.utc)
        if not self._should_attach(template_id=template_id, rng=rng):
            return None

        decision = self._mode_decider.decide(pillar_id=pillar_id, template_id=template_id, rng=rng)
        size = self._output_size()

        attempts = 1
        if self._settings.validation.enabled and self._validator:
            attempts = max(1, int(self._settings.validation.max_attempts))
        for attempt_idx in range(attempts):
            prompt = self._prompt_builder.build(mode=decision.mode, strictness=attempt_idx)
            try:
                bg = self._provider.generate(request=BackgroundRequest(prompt=prompt.prompt, mode=decision.mode, output_size=size))
            except ProviderError as exc:
                self._logger.warning("Image generation failed (background): %s", str(exc))
                return None

            if self._settings.validation.enabled and self._validator and self._character:
                verdict = self._validator.validate_background(image=bg, mode=decision.mode, character=self._character)
                if not verdict.accept:
                    self._logger.info("Rejected generated background mode=%s issues=%s", decision.mode.value, verdict.issues)
                    continue

            text = self._headline_extractor.extract(post_text=post_text, pillar_id=pillar_id, template_id=template_id)
            logo_path = self._resolve_path(self._settings.logo_path)
            font_path = self._resolve_path(self._settings.font_path)

            final = self._renderer.render(
                background=bg,
                headline=text.headline,
                subtext=text.subtext,
                output_size=size,
                logo_path=logo_path,
                font_path=(font_path if font_path.exists() else None),
            )

            output_path = self._build_output_path(post_id=post_id, now=now)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            final.save(output_path, format="PNG", optimize=True)
            return ImageAttachment(image_mode=decision.mode.value, image_path=self._rel_path(output_path))

        return None

    def _should_attach(self, *, template_id: str, rng: Random) -> bool:
        template = (template_id or "").strip()
        if template and template in set(self._settings.force_for_templates or []):
            return True
        return rng.random() < float(self._settings.attach_to_post_probability)

    def _output_size(self) -> Tuple[int, int]:
        w = int((self._settings.image_size or [1080, 1080])[0])
        h = int((self._settings.image_size or [1080, 1080])[1])
        return w, h

    def _build_output_path(self, *, post_id: str, now: datetime) -> Path:
        safe_id = (post_id or "post").replace("/", "-").replace("\\", "-")[:32]
        stamp = now.astimezone(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"post_{stamp}_{safe_id[:8]}.png"
        return self._project_root / self._settings.output_dir / filename

    def _resolve_path(self, maybe_rel: str) -> Path:
        raw = (maybe_rel or "").strip()
        if not raw:
            return self._project_root
        p = Path(raw)
        return p if p.is_absolute() else (self._project_root / p)

    def _rel_path(self, absolute_path: Path) -> str:
        try:
            rel = absolute_path.relative_to(self._project_root).as_posix()
        except Exception:
            rel = absolute_path.as_posix()
        return rel


