from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


class CharacterSpecError(RuntimeError):
    pass


def _as_str(value: Any) -> str:
    return str(value or "").strip()


def _as_list_str(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [_as_str(x) for x in value if _as_str(x)]


@dataclass(frozen=True)
class CharacterSpec:
    character_id: str
    display_name: str
    species: str
    style: str
    anchors: List[str]
    forbidden: List[str]

    @staticmethod
    def load(path: Path) -> "CharacterSpec":
        if not path.exists():
            raise CharacterSpecError(f"Missing character spec: {path}")
        try:
            raw: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise CharacterSpecError(f"Invalid character spec JSON: {path}") from exc

        character_id = _as_str(raw.get("character_id"))
        display_name = _as_str(raw.get("display_name"))
        species = _as_str(raw.get("species"))
        style = _as_str(raw.get("style"))

        face = raw.get("face") or {}
        body = raw.get("body") or {}
        fur = raw.get("fur") or {}
        wardrobe = raw.get("wardrobe") or {}
        lighting = raw.get("lighting") or {}
        tone = raw.get("tone") or {}

        anchors = [
            species or "western lowland gorilla",
            style or "hyper-realistic cinematic",
            _as_str(face.get("shape")),
            _as_str(body.get("build")),
            _as_str(body.get("posture")),
            _as_str(fur.get("color")),
            _as_str(fur.get("texture")),
            f"accent color { _as_str(wardrobe.get('accent_color')) }" if _as_str(wardrobe.get("accent_color")) else "",
            _as_str(lighting.get("style")),
            _as_str(lighting.get("temperature")),
            _as_str(tone.get("vibe")),
        ]
        anchors = [a for a in anchors if a]

        forbidden = []
        forbidden.extend(_as_list_str(face.get("emotion_limits")))
        forbidden.extend(_as_list_str(wardrobe.get("forbidden")))
        forbidden.extend(_as_list_str(lighting.get("forbidden")))
        forbidden.extend(_as_list_str((raw.get("backgrounds") or {}).get("forbidden")))
        forbidden.extend(_as_list_str(tone.get("not_allowed")))
        forbidden = [f for f in forbidden if f]

        if not character_id:
            raise CharacterSpecError("character_id is required")
        return CharacterSpec(
            character_id=character_id,
            display_name=display_name or character_id,
            species=species or "western lowland gorilla",
            style=style or "hyper-realistic cinematic",
            anchors=anchors,
            forbidden=forbidden,
        )

    def prompt_anchors(self) -> str:
        parts = [
            f"{self.style} {self.species}",
            "deep charcoal black fur, ultra-detailed short dense fur texture",
            "athletic powerful build, dominant posture",
            "intense focused expression, no goofy smiles, no cartoon exaggeration",
            "dark tones with neon green accents, cinematic stadium or studio lighting",
        ]
        return ", ".join([p for p in parts if p])


