from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Literal, Optional

QueueItemType = Literal["single", "thread"]
ImageModeName = Literal["quote_card", "analysis_card", "persona", "ui_tease", "generic"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_iso8601(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso8601(value: str) -> datetime:
    raw = (value or "").strip()
    if not raw:
        return utc_now()
    raw = raw.replace("Z", "+00:00")
    return datetime.fromisoformat(raw)


def text_sha256(value: str) -> str:
    normalized = (value or "").strip().encode("utf-8")
    return sha256(normalized).hexdigest()


@dataclass(frozen=True)
class QueueItem:
    id: str
    type: QueueItemType
    pillar_id: str
    template_id: str
    score: float
    recommended_tier: str
    created_at: str
    text: Optional[str] = None
    tweets: Optional[List[str]] = None
    topic: Optional[str] = None
    image_mode: Optional[ImageModeName] = None
    image_path: Optional[str] = None

    def to_outbox_dict(self) -> Dict[str, Any]:
        base: Dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "pillar_id": self.pillar_id,
            "template_id": self.template_id,
            "score": self.score,
            "recommended_tier": self.recommended_tier,
            "created_at": self.created_at,
        }
        if self.image_mode:
            base["image_mode"] = self.image_mode
        if self.image_path:
            base["image_path"] = self.image_path
        if self.type == "single":
            base["text"] = self.text or ""
            return base
        base["tweets"] = list(self.tweets or [])
        base["topic"] = self.topic or ""
        return base

    def flattened_text(self) -> str:
        if self.type == "single":
            return self.text or ""
        return "\n".join(self.tweets or [])


@dataclass(frozen=True)
class PostedRecord:
    id: str
    type: QueueItemType
    posted_at: str
    tweet_ids: List[str]
    text_hash: str
    pillar_id: str
    template_id: str
    score: float
    recommended_tier: str
    is_disclaimer: bool
    is_analysis: bool
    analysis_slug: Optional[str] = None
    text: Optional[str] = None
    tweets: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "posted_at": self.posted_at,
            "tweet_ids": list(self.tweet_ids),
            "text_hash": self.text_hash,
            "pillar_id": self.pillar_id,
            "template_id": self.template_id,
            "score": self.score,
            "recommended_tier": self.recommended_tier,
            "is_disclaimer": self.is_disclaimer,
            "is_analysis": self.is_analysis,
            "analysis_slug": self.analysis_slug,
        }
        if self.type == "single" and self.text is not None:
            payload["text"] = self.text
        if self.type == "thread" and self.tweets is not None:
            payload["tweets"] = list(self.tweets)
        return payload


@dataclass(frozen=True)
class AnalysisFeedItem:
    slug: str
    angle: str
    key_points: List[str]
    risk_note: Optional[str]
    cta_url: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AnalysisFeedItem":
        return AnalysisFeedItem(
            slug=str(data.get("slug") or "").strip(),
            angle=str(data.get("angle") or "").strip(),
            key_points=[str(x).strip() for x in (data.get("key_points") or []) if str(x).strip()],
            risk_note=(str(data.get("risk_note")).strip() if data.get("risk_note") else None),
            cta_url=str(data.get("cta_url") or "").strip(),
        )


@dataclass(frozen=True)
class PublishResult:
    success: bool
    tweet_ids: List[str]
    error: Optional[str] = None
    pause_until: Optional[datetime] = None


