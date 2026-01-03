from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from random import Random

from PIL import Image

from src.images.font_loader import FontLoader
from src.images.headline_extractor import HeadlineExtractor
from src.images.mode_decider import ImageModeDecider
from src.images.pipeline import ImagePipeline
from src.images.prompt_builder import ImagePromptBuilder
from src.images.providers.base import BackgroundImageProvider, BackgroundRequest
from src.images.renderer import ImageRenderer
from src.settings import ImageValidationSettings, ImagesSettings


class SolidBackgroundProvider(BackgroundImageProvider):
    def generate(self, *, request: BackgroundRequest) -> Image.Image:
        img = Image.new("RGBA", request.output_size, (12, 12, 12, 255))
        return img


def _write_logo(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    logo = Image.new("RGBA", (256, 128), (0, 255, 0, 180))
    logo.save(path, format="PNG")


def test_headline_extractor_scrubs_numbers_and_limits_words() -> None:
    extractor = HeadlineExtractor()
    text = "Quick math that saves your bankroll: even a 60% leg x4 is only 13% over time."
    out = extractor.extract(post_text=text, pillar_id="betting_discipline", template_id="unknown_template")
    assert out.headline
    assert any(ch.isdigit() for ch in out.headline) is False
    words = out.headline.split()
    assert 8 <= len(words) <= 12


def test_headline_extractor_uses_analysis_template_mapping() -> None:
    extractor = HeadlineExtractor()
    out = extractor.extract(post_text="ignored", pillar_id="analysis_excerpts", template_id="analysis_matchup_angle")
    assert out.headline.startswith("MATCHUP CONTEXT")


def test_pipeline_writes_final_image(tmp_path: Path) -> None:
    project_root = tmp_path / "bot"
    logo_path = project_root / "images" / "logos" / "parlay_gorilla_logo.png"
    _write_logo(logo_path)

    settings = ImagesSettings(
        enabled=True,
        provider="openai",
        output_dir="images/generated",
        image_size=[1080, 1080],
        attach_to_post_probability=1.0,
        force_for_templates=[],
        logo_path="images/logos/parlay_gorilla_logo.png",
        font_path="images/templates/fonts/Inter-Bold.ttf",
        character_spec_path="",
        validation=ImageValidationSettings(enabled=False, provider="openai", model="gpt-4o-mini", max_attempts=1),
        openai_api_key="test",
    )

    pipeline = ImagePipeline(
        project_root=project_root,
        settings=settings,
        provider=SolidBackgroundProvider(),
        mode_decider=ImageModeDecider(),
        prompt_builder=ImagePromptBuilder(),
        headline_extractor=HeadlineExtractor(),
        renderer=ImageRenderer(font_loader=FontLoader()),
    )

    fixed_now = datetime(2026, 1, 2, 9, 15, tzinfo=timezone.utc)
    attachment = pipeline.maybe_generate(
        post_id="abc123",
        post_text="Keep your unit size boring. Discipline wins.",
        pillar_id="betting_discipline",
        template_id="discipline_unit_size",
        rng=Random(1),
        now=fixed_now,
    )
    assert attachment is not None
    assert attachment.image_mode
    assert attachment.image_path.endswith(".png")
    out_path = project_root / attachment.image_path
    assert out_path.exists()
    img = Image.open(out_path)
    assert img.size == (1080, 1080)


