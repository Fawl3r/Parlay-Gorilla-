from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from random import Random
from typing import Any, Dict, List, Optional


class ContentError(RuntimeError):
    pass


@dataclass(frozen=True)
class PillarDefinition:
    id: str
    name: str
    weight: float
    suggested_templates: List[str]


@dataclass(frozen=True)
class TemplateDefinition:
    id: str
    type: str  # single | thread
    text: str
    is_disclaimer: bool
    is_analysis: bool
    base_score: float


@dataclass(frozen=True)
class HookDefinition:
    id: str
    text: str
    weight: float


@dataclass(frozen=True)
class SeasonalMode:
    id: str
    name: str
    months: List[int]
    pillar_multipliers: Dict[str, float]


class ContentLibrary:
    def __init__(self, content_dir: Path) -> None:
        self._content_dir = content_dir
        self._pillars: List[PillarDefinition] = []
        self._templates: Dict[str, TemplateDefinition] = {}
        self._hooks: List[HookDefinition] = []
        self._seasonal_modes: List[SeasonalMode] = []
        self._banned_phrases: List[str] = []
        self._loaded = False

    def load(self) -> "ContentLibrary":
        if self._loaded:
            return self
        self._pillars = [self._parse_pillar(x) for x in self._read_json("pillars.json")]
        self._templates = {t.id: t for t in [self._parse_template(x) for x in self._read_json("templates.json")]}
        self._hooks = [self._parse_hook(x) for x in self._read_json("hooks.json")]
        self._seasonal_modes = [self._parse_seasonal(x) for x in self._read_json("seasonal_modes.json")]
        self._banned_phrases = [str(x).strip() for x in self._read_json("banned_phrases.json") if str(x).strip()]
        self._loaded = True
        return self

    @property
    def pillars(self) -> List[PillarDefinition]:
        return list(self._pillars)

    @property
    def templates(self) -> Dict[str, TemplateDefinition]:
        return dict(self._templates)

    @property
    def hooks(self) -> List[HookDefinition]:
        return list(self._hooks)

    @property
    def banned_phrases(self) -> List[str]:
        return list(self._banned_phrases)

    def get_template(self, template_id: str) -> TemplateDefinition:
        if template_id not in self._templates:
            raise ContentError(f"Unknown template_id: {template_id}")
        return self._templates[template_id]

    def choose_pillar(self, rng: Random, now: datetime) -> PillarDefinition:
        multipliers = self._active_pillar_multipliers(now)
        weighted: List[tuple[PillarDefinition, float]] = []
        for p in self._pillars:
            weighted.append((p, float(p.weight) * float(multipliers.get(p.id, 1.0))))
        return _weighted_choice(rng, weighted)

    def choose_hook(self, rng: Random, *, exclude_texts: List[str]) -> Optional[HookDefinition]:
        eligible: List[tuple[HookDefinition, float]] = []
        for hook in self._hooks:
            if hook.text in exclude_texts:
                continue
            eligible.append((hook, float(hook.weight)))
        if not eligible:
            return None
        return _weighted_choice(rng, eligible)

    def _active_pillar_multipliers(self, now: datetime) -> Dict[str, float]:
        month = int(now.month)
        for mode in self._seasonal_modes:
            if month in mode.months:
                return dict(mode.pillar_multipliers)
        return {}

    def _read_json(self, filename: str) -> Any:
        path = self._content_dir / filename
        if not path.exists():
            raise ContentError(f"Missing content file: {path}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ContentError(f"Failed to parse JSON: {path}") from exc

    def _parse_pillar(self, raw: Dict[str, Any]) -> PillarDefinition:
        return PillarDefinition(
            id=str(raw.get("id") or "").strip(),
            name=str(raw.get("name") or "").strip(),
            weight=float(raw.get("weight") or 0.0),
            suggested_templates=[str(x) for x in (raw.get("suggested_templates") or [])],
        )

    def _parse_template(self, raw: Dict[str, Any]) -> TemplateDefinition:
        return TemplateDefinition(
            id=str(raw.get("id") or "").strip(),
            type=str(raw.get("type") or "single").strip(),
            text=str(raw.get("text") or ""),
            is_disclaimer=bool(raw.get("is_disclaimer", False)),
            is_analysis=bool(raw.get("is_analysis", False)),
            base_score=float(raw.get("base_score") or 0.0),
        )

    def _parse_hook(self, raw: Dict[str, Any]) -> HookDefinition:
        return HookDefinition(
            id=str(raw.get("id") or "").strip(),
            text=str(raw.get("text") or "").strip(),
            weight=float(raw.get("weight") or 1.0),
        )

    def _parse_seasonal(self, raw: Dict[str, Any]) -> SeasonalMode:
        return SeasonalMode(
            id=str(raw.get("id") or "").strip(),
            name=str(raw.get("name") or "").strip(),
            months=[int(x) for x in (raw.get("months") or [])],
            pillar_multipliers={str(k): float(v) for k, v in (raw.get("pillar_multipliers") or {}).items()},
        )


def _weighted_choice(rng: Random, weighted: List[tuple[Any, float]]):
    total = sum(max(0.0, w) for _, w in weighted)
    if total <= 0:
        return weighted[0][0]
    roll = rng.random() * total
    acc = 0.0
    for item, weight in weighted:
        acc += max(0.0, weight)
        if roll <= acc:
            return item
    return weighted[-1][0]


