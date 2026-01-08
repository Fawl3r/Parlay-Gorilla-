from __future__ import annotations

import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from social_bot.memory_store import BotMemory, MemoryStore
from social_bot.post_generator import PostType


ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class ImageChoice:
    path: Path
    memory_path: str
    reason: str


class ImageLibrary:
    """
    Manual image library.

    Selection rules:
    - Folders are under images_root/{education,analysis,football,basketball,baseball,soccer,hockey,general}
    - Avoid reusing last N images (N=8)
    - Allowed extensions: png/jpg/jpeg/webp
    - Max file size: 8MB
    - If no image available, return None
    """

    def __init__(self, *, images_root: Path, store: MemoryStore) -> None:
        self._root = images_root
        self._store = store

    def choose(
        self,
        *,
        post_type: PostType,
        analysis_slug: Optional[str],
        analysis_league: Optional[str],
        memory: BotMemory,
        rng: random.Random,
        always_attach: bool,
        attach_probability: float,
    ) -> Optional[ImageChoice]:
        if not always_attach and rng.random() >= float(attach_probability):
            return None

        sport = self._sport_from_context(slug=analysis_slug, league=analysis_league)
        topic = self._topic_from_post_type(post_type=post_type, has_analysis=bool(analysis_slug))

        candidates_dirs = self._candidate_dirs(topic=topic, sport=sport)
        recent = set(self._store.recent_media_paths(memory, limit=8))

        files: list[Path] = []
        for d in candidates_dirs:
            files.extend(self._list_images(d))

        # Filter invalid / too-large / recently used.
        filtered: list[Path] = []
        for p in files:
            rel = self._rel_media_path(p)
            if rel and rel in recent:
                continue
            try:
                if p.stat().st_size > MAX_BYTES:
                    continue
            except Exception:
                continue
            filtered.append(p)

        if not filtered and files:
            # If everything is "recent", allow reuse but still enforce size/ext rules.
            filtered = [p for p in files if self._is_allowed(p)]

        if not filtered:
            return None

        chosen = filtered[int(rng.random() * len(filtered))]
        return ImageChoice(path=chosen, memory_path=self._rel_media_path(chosen), reason=f"topic={topic} sport={sport}")

    def _candidate_dirs(self, *, topic: str, sport: str) -> list[Path]:
        # Folder priority rules
        dirs: list[Path] = []
        if topic == "education":
            dirs.append(self._root / "education")
            dirs.append(self._root / sport)
            dirs.append(self._root / "general")
        elif topic == "analysis":
            dirs.append(self._root / "analysis")
            dirs.append(self._root / sport)
            dirs.append(self._root / "general")
        else:
            dirs.append(self._root / sport)
            dirs.append(self._root / "general")
        # Only include existing dirs
        return [d for d in dirs if d.exists() and d.is_dir()]

    @staticmethod
    def _topic_from_post_type(*, post_type: PostType, has_analysis: bool) -> str:
        if post_type == PostType.EXAMPLE_PARLAY:
            return "parlay"
        if has_analysis and post_type in {PostType.TRAP_ALERT, PostType.EDGE_EXPLAINER}:
            return "analysis"
        if post_type in {PostType.PARLAY_MATH, PostType.EDGE_EXPLAINER}:
            return "education"
        return "general"

    @staticmethod
    def _sport_from_context(*, slug: Optional[str], league: Optional[str]) -> str:
        league_norm = (league or "").strip().lower()
        slug_norm = (slug or "").strip().lstrip("/").lower()
        prefix = slug_norm.split("/", 1)[0] if "/" in slug_norm else slug_norm

        # League-based mapping first
        if league_norm in {"nfl", "cfb", "ncaaf"}:
            return "football"
        if league_norm in {"nba", "wnba", "ncaab"}:
            return "basketball"
        if league_norm in {"mlb"}:
            return "baseball"
        if league_norm in {"nhl"}:
            return "hockey"
        if league_norm in {"soccer", "mls", "epl", "uefa", "fifa"}:
            return "soccer"

        # Slug prefix mapping
        if prefix in {"nfl", "cfb", "ncaaf"}:
            return "football"
        if prefix in {"nba", "wnba", "ncaab"}:
            return "basketball"
        if prefix in {"mlb"}:
            return "baseball"
        if prefix in {"nhl"}:
            return "hockey"
        if prefix in {"soccer"}:
            return "soccer"
        return "general"

    def _list_images(self, directory: Path) -> list[Path]:
        try:
            items = list(directory.iterdir())
        except Exception:
            return []
        out: list[Path] = []
        for p in items:
            if p.is_file() and self._is_allowed(p):
                out.append(p)
        return out

    @staticmethod
    def _is_allowed(path: Path) -> bool:
        ext = path.suffix.lower()
        if ext not in ALLOWED_EXTS:
            return False
        try:
            # Skip zero-size files
            return path.stat().st_size > 0
        except Exception:
            return False

    def _rel_media_path(self, path: Path) -> str:
        try:
            rel = path.relative_to(self._root)
            # Store as "images/..." for stability
            return str(Path("images") / rel).replace("\\", "/")
        except Exception:
            return str(path).replace("\\", "/")


def ensure_image_folders(images_root: Path) -> None:
    folders = [
        "football",
        "basketball",
        "baseball",
        "soccer",
        "hockey",
        "education",
        "analysis",
        "general",
    ]
    for name in folders:
        d = images_root / name
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            try:
                keep.write_text("keep\n", encoding="utf-8")
            except Exception:
                pass


