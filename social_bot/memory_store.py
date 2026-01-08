from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso8601(value: str) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


@dataclass(frozen=True)
class MemoryPost:
    ts_iso: str
    post_type: str
    text: str
    tweet_id: str
    analysis_slug: Optional[str]
    humor_allowed: bool
    media_path: Optional[str] = None

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "MemoryPost":
        return MemoryPost(
            ts_iso=str(raw.get("ts_iso") or ""),
            post_type=str(raw.get("post_type") or ""),
            text=str(raw.get("text") or ""),
            tweet_id=str(raw.get("tweet_id") or ""),
            analysis_slug=(str(raw.get("analysis_slug")) if raw.get("analysis_slug") else None),
            humor_allowed=bool(raw.get("humor_allowed") or False),
            media_path=(str(raw.get("media_path")) if raw.get("media_path") else None),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts_iso": self.ts_iso,
            "post_type": self.post_type,
            "text": self.text,
            "tweet_id": self.tweet_id,
            "analysis_slug": self.analysis_slug,
            "humor_allowed": self.humor_allowed,
            "media_path": self.media_path,
        }


@dataclass(frozen=True)
class BotMemory:
    version: int
    posts: list[MemoryPost]

    @staticmethod
    def empty() -> "BotMemory":
        return BotMemory(version=1, posts=[])

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "BotMemory":
        posts_raw = raw.get("posts") if isinstance(raw, dict) else None
        posts: list[MemoryPost] = []
        if isinstance(posts_raw, list):
            for p in posts_raw:
                if isinstance(p, dict):
                    posts.append(MemoryPost.from_dict(p))
        return BotMemory(version=int(raw.get("version") or 1), posts=posts)

    def to_dict(self) -> dict[str, Any]:
        return {"version": self.version, "posts": [p.to_dict() for p in self.posts]}


class MemoryStore:
    def __init__(self, *, path: Path, timezone_name: str) -> None:
        self._path = path
        self._tz = ZoneInfo(timezone_name)

    def load(self) -> BotMemory:
        if not self._path.exists():
            return BotMemory.empty()
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return BotMemory.empty()
            return BotMemory.from_dict(raw)
        except Exception:
            return BotMemory.empty()

    def save(self, memory: BotMemory) -> None:
        self._path.write_text(json.dumps(memory.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def local_day(self, ts: datetime) -> date:
        return ts.astimezone(self._tz).date()

    def posts_today_count(self, memory: BotMemory, *, now: Optional[datetime] = None) -> int:
        now_dt = now or utc_now()
        today = self.local_day(now_dt)
        count = 0
        for p in memory.posts:
            dt = _parse_iso8601(p.ts_iso)
            if dt and self.local_day(dt) == today:
                count += 1
        return count

    def recent_texts(self, memory: BotMemory, *, limit: int = 50) -> list[str]:
        return [p.text for p in memory.posts[-int(limit) :] if p.text]

    def recent_media_paths(self, memory: BotMemory, *, limit: int = 8) -> list[str]:
        paths: list[str] = []
        for p in reversed(memory.posts):
            if p.media_path:
                paths.append(str(p.media_path))
            if len(paths) >= int(limit):
                break
        return list(reversed(paths))

    def slug_used_within_hours(self, memory: BotMemory, *, slug: str, hours: int, now: Optional[datetime] = None) -> bool:
        slug_norm = (slug or "").strip().lstrip("/")
        if not slug_norm:
            return False
        now_dt = now or utc_now()
        window_seconds = float(max(0, int(hours))) * 3600.0
        for p in reversed(memory.posts):
            if not p.analysis_slug or p.analysis_slug.strip().lstrip("/") != slug_norm:
                continue
            dt = _parse_iso8601(p.ts_iso)
            if not dt:
                continue
            if (now_dt - dt).total_seconds() <= window_seconds:
                return True
        return False

    def humor_ratio_recent(self, memory: BotMemory, *, window: int = 20) -> float:
        posts = memory.posts[-int(window) :] if window > 0 else []
        if not posts:
            return 0.0
        used = sum(1 for p in posts if p.humor_allowed)
        return float(used) / float(len(posts))

    def record_post(
        self,
        memory: BotMemory,
        *,
        now: datetime,
        post_type: str,
        text: str,
        tweet_id: str,
        analysis_slug: Optional[str],
        humor_allowed: bool,
        media_path: Optional[str] = None,
        keep_last: int = 300,
    ) -> BotMemory:
        entry = MemoryPost(
            ts_iso=now.isoformat(),
            post_type=str(post_type),
            text=str(text),
            tweet_id=str(tweet_id),
            analysis_slug=(analysis_slug.strip().lstrip("/") if analysis_slug else None),
            humor_allowed=bool(humor_allowed),
            media_path=(str(media_path) if media_path else None),
        )
        posts = list(memory.posts) + [entry]
        if keep_last > 0 and len(posts) > int(keep_last):
            posts = posts[-int(keep_last) :]
        return BotMemory(version=memory.version, posts=posts)


