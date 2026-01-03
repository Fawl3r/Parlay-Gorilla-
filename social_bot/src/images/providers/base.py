from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple

from PIL import Image

from src.images.image_mode import ImageMode


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class BackgroundRequest:
    prompt: str
    mode: ImageMode
    output_size: Tuple[int, int]


class BackgroundImageProvider(ABC):
    @abstractmethod
    def generate(self, *, request: BackgroundRequest) -> Image.Image:
        raise NotImplementedError


