from __future__ import annotations

import base64
import io
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from PIL import Image

from src.images.character_spec import CharacterSpec
from src.images.image_mode import ImageMode
from src.images.validators.base import ValidationResult, VisionValidator


@dataclass(frozen=True)
class OpenAIVisionConfig:
    api_key: str
    model: str
    base_url: str
    timeout_seconds: float


class OpenAIVisionValidator(VisionValidator):
    def __init__(self, *, config: OpenAIVisionConfig, http_client: Optional[httpx.Client] = None) -> None:
        self._config = config
        self._http = http_client
        self._logger = logging.getLogger("social_bot")

    def validate_background(self, *, image: Image.Image, mode: ImageMode, character: CharacterSpec) -> ValidationResult:
        if not self._config.api_key:
            return ValidationResult(accept=True, confidence=0.0, issues=["validator_missing_api_key"], notes="Skipped validation")

        data_url = self._to_png_data_url(image)
        system = (
            "You are a strict brand-safety and consistency validator for a sports betting brand.\n"
            "You must return ONLY valid JSON.\n\n"
            "Hard rejects:\n"
            "- Any team logos, team names, uniforms, mascots, or recognizable athletes\n"
            "- Any sportsbook or third-party brand logos\n"
            "- Any readable text, letters, numbers, odds, or signage\n"
            "- Cartoon or illustrated style (must be cinematic premium)\n"
        )

        user_text = self._build_user_prompt(mode=mode, character=character)
        payload: Dict[str, Any] = {
            "model": self._config.model,
            "messages": [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        }
        headers = {"Authorization": f"Bearer {self._config.api_key}", "Content-Type": "application/json"}
        url = f"{self._config.base_url.rstrip('/')}/chat/completions"

        client = self._http or httpx.Client(timeout=self._config.timeout_seconds)
        try:
            resp = client.post(url, headers=headers, json=payload)
        finally:
            if self._http is None:
                client.close()

        if resp.status_code >= 400:
            self._logger.warning("Vision validation failed (HTTP %s); allowing image.", resp.status_code)
            return ValidationResult(accept=True, confidence=0.0, issues=["validator_http_error"], notes=f"HTTP {resp.status_code}")

        try:
            raw = resp.json() or {}
            content = str(((raw.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
            parsed = json.loads(content) if content else {}
            return self._parse_result(parsed)
        except Exception as exc:
            self._logger.warning("Vision validation returned invalid JSON; allowing image. error=%s", str(exc))
            return ValidationResult(accept=True, confidence=0.0, issues=["validator_parse_error"], notes="Invalid JSON")

    def _build_user_prompt(self, *, mode: ImageMode, character: CharacterSpec) -> str:
        base_rules = (
            "Evaluate this image as a BACKGROUND image for a social post.\n"
            "It must be on-brand for Parlay Gorilla: dark, premium, cinematic, with subtle neon green accents.\n"
            "It must contain no readable text and no logos/teams/brands.\n"
            "Return JSON with keys: accept (boolean), confidence (0..1), issues (array of strings), notes (string).\n"
        )
        if mode == ImageMode.persona:
            return (
                base_rules
                + "\nPersona-specific rules:\n"
                + f"- If a gorilla is present, it should match: {character.prompt_anchors()}.\n"
                + "- Reject if cartoonish, goofy smile, chibi proportions, or cheap meme vibe.\n"
            )
        if mode == ImageMode.analysis_card:
            return (
                base_rules
                + "\nAnalysis-specific rules:\n"
                + "- Background should look like abstract sports analytics / dashboards, but with NO readable UI text.\n"
            )
        if mode == ImageMode.ui_tease:
            return (
                base_rules
                + "\nUI-tease rules:\n"
                + "- Background can suggest a dark app dashboard, but NO readable UI text, no letters, no numbers.\n"
            )
        return base_rules

    def _parse_result(self, data: Dict[str, Any]) -> ValidationResult:
        accept = bool(data.get("accept", False))
        try:
            confidence = float(data.get("confidence", 0.0))
        except Exception:
            confidence = 0.0
        issues_raw = data.get("issues") or []
        issues = [str(x) for x in issues_raw if str(x).strip()] if isinstance(issues_raw, list) else []
        notes = str(data.get("notes") or "").strip()
        if accept and confidence <= 0:
            confidence = 0.5
        return ValidationResult(accept=accept, confidence=max(0.0, min(1.0, confidence)), issues=issues, notes=notes)

    def _to_png_data_url(self, image: Image.Image) -> str:
        buf = io.BytesIO()
        image.convert("RGBA").save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"


