from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from PIL import Image

from src.images.providers.base import BackgroundImageProvider, BackgroundRequest, ProviderError


@dataclass(frozen=True)
class OpenAIProviderConfig:
    api_key: str
    model: str
    base_url: str
    timeout_seconds: float


class OpenAIBackgroundProvider(BackgroundImageProvider):
    def __init__(self, *, config: OpenAIProviderConfig, http_client: Optional[httpx.Client] = None) -> None:
        self._config = config
        self._http = http_client

    def generate(self, *, request: BackgroundRequest) -> Image.Image:
        if not self._config.api_key:
            raise ProviderError("Missing OPENAI_API_KEY")

        api_size = self._api_size_for(request.output_size)
        payload: Dict[str, Any] = {
            "model": self._config.model,
            "prompt": request.prompt,
            "size": api_size,
            "n": 1,
            "response_format": "b64_json",
        }
        headers = {"Authorization": f"Bearer {self._config.api_key}", "Content-Type": "application/json"}
        url = f"{self._config.base_url.rstrip('/')}/images/generations"

        client = self._http or httpx.Client(timeout=self._config.timeout_seconds)
        try:
            resp = client.post(url, headers=headers, json=payload)
        finally:
            if self._http is None:
                client.close()

        if resp.status_code >= 400:
            raise ProviderError(f"OpenAI image generation failed (HTTP {resp.status_code})")

        try:
            raw = resp.json()
            b64 = str(((raw or {}).get("data") or [{}])[0].get("b64_json") or "").strip()
            if not b64:
                raise ProviderError("OpenAI image generation returned no image data")
            image = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGBA")
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("OpenAI image generation returned invalid data") from exc

        if image.size != request.output_size:
            image = image.resize(request.output_size, resample=Image.Resampling.LANCZOS)
        return image

    def _api_size_for(self, output_size) -> str:
        w, h = int(output_size[0]), int(output_size[1])
        if w == h:
            return "1024x1024"
        if w > h:
            return "1792x1024"
        return "1024x1792"


