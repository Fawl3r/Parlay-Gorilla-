from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from PIL import Image

from src.images.character_spec import CharacterSpec
from src.images.image_mode import ImageMode


@dataclass(frozen=True)
class ValidationResult:
    accept: bool
    confidence: float
    issues: List[str]
    notes: str = ""


class VisionValidator(ABC):
    @abstractmethod
    def validate_background(self, *, image: Image.Image, mode: ImageMode, character: CharacterSpec) -> ValidationResult:
        raise NotImplementedError


