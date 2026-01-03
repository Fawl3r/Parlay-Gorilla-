from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlparse, urlencode

import httpx
import re

from src.models import AnalysisFeedItem, parse_iso8601, to_iso8601


class SiteFeedError(RuntimeError):
    pass


@dataclass(frozen=True)
class FeedCache:
    fetched_at: Optional[str]
    expires_at: Optional[str]
    items: List[Dict[str, Any]]
    used_slugs: Dict[str, str]
    upcoming_fetched_at: Optional[str]
    upcoming_expires_at: Optional[str]
    upcoming_items: List[Dict[str, Any]]


class SiteFeedClient:
    def __init__(
        self,
        *,
        analysis_feed_url: str,
        cache_path: Path,
        cache_ttl_seconds: int,
        slug_reuse_cooldown_hours: int,
        redirect_base_url: str,
        ab_variants: List[str],
        upcoming_sport: str = "nfl",
        upcoming_limit: int = 20,
        timeout_seconds: float,
    ) -> None:
        self._analysis_feed_url = analysis_feed_url.strip()
        self._cache_path = cache_path
        self._cache_ttl = timedelta(seconds=int(cache_ttl_seconds))
        self._slug_cooldown = timedelta(hours=int(slug_reuse_cooldown_hours))
        self._redirect_base_url = redirect_base_url.strip()
        self._ab_variants = [v for v in ab_variants if str(v).strip()] or ["a", "b"]
        self._upcoming_sport = str(upcoming_sport or "nfl").strip().lower()
        self._upcoming_limit = int(upcoming_limit or 20)
        self._timeout_seconds = float(timeout_seconds)
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)

    def get_injectable_item(
        self,
        *,
        now: datetime,
        posted_raw: List[dict],
    ) -> Optional[Tuple[AnalysisFeedItem, str]]:
        items = self._get_items(now=now)
        if not items:
            return None

        used = self._build_used_slugs(now=now, posted_raw=posted_raw)
        for raw in items:
            item = AnalysisFeedItem.from_dict(raw)
            if not item.slug:
                continue
            last_used = used.get(item.slug)
            if last_used and now - last_used < self._slug_cooldown:
                continue
            variant = self._pick_variant(now=now, slug=item.slug)
            self._mark_used(slug=item.slug, now=now)
            return item, variant
        return None

    def get_upcoming_matchup_link(
        self,
        *,
        now: datetime,
        posted_raw: List[dict],
    ) -> Optional[Tuple[str, str, str]]:
        items = self._get_upcoming_items(now=now)
        if not items:
            return None

        used = self._build_used_slugs(now=now, posted_raw=posted_raw)
        for raw in items:
            if not isinstance(raw, dict):
                continue
            slug = str(raw.get("slug") or "").strip()
            if not slug:
                continue
            if not self._slug_is_safe(slug):
                continue
            last_used = used.get(slug)
            if last_used and now - last_used < self._slug_cooldown:
                continue
            matchup = str(raw.get("matchup") or slug).strip()
            variant = self._pick_variant(now=now, slug=slug)
            self._mark_used(slug=slug, now=now)
            return matchup, self.build_tracking_url(slug=slug, variant=variant), slug
        return None

    def _slug_is_safe(self, slug: str) -> bool:
        s = (slug or "").strip().lower()
        if not s:
            return False
        # Guard against obviously broken/placeholder slugs that would create dead links.
        if "week-none" in s or "week-null" in s or "undefined" in s:
            return False
        # If it looks like an NFL week slug, require a numeric week.
        if "week-" in s and not re.search(r"week-\d+", s):
            return False
        return True

    def build_tracking_url(self, *, slug: str, variant: str) -> str:
        base = (self._redirect_base_url or self._derive_base_from_feed_url()).rstrip("/")
        safe_slug = quote(slug.lstrip("/"), safe="/-_.")
        query = urlencode({"v": variant})
        return f"{base}/r/{safe_slug}?{query}"

    def _get_items(self, *, now: datetime) -> List[Dict[str, Any]]:
        cache = self._load_cache()
        if cache.expires_at:
            try:
                expires = parse_iso8601(cache.expires_at)
                if now < expires:
                    return cache.items
            except Exception:
                pass
        if not self._analysis_feed_url:
            return cache.items
        fetched = self._fetch_remote()
        next_cache = FeedCache(
            fetched_at=to_iso8601(now),
            expires_at=to_iso8601(now + self._cache_ttl),
            items=fetched,
            used_slugs=cache.used_slugs,
            upcoming_fetched_at=cache.upcoming_fetched_at,
            upcoming_expires_at=cache.upcoming_expires_at,
            upcoming_items=cache.upcoming_items,
        )
        self._save_cache(next_cache)
        return fetched

    def _get_upcoming_items(self, *, now: datetime) -> List[Dict[str, Any]]:
        cache = self._load_cache()
        if cache.upcoming_expires_at:
            try:
                expires = parse_iso8601(cache.upcoming_expires_at)
                if now < expires:
                    return cache.upcoming_items
            except Exception:
                pass

        base = (self._redirect_base_url or self._derive_base_from_feed_url()).rstrip("/")
        if not base:
            return cache.upcoming_items

        fetched = self._fetch_upcoming_remote(base=base)
        next_cache = FeedCache(
            fetched_at=cache.fetched_at,
            expires_at=cache.expires_at,
            items=cache.items,
            used_slugs=cache.used_slugs,
            upcoming_fetched_at=to_iso8601(now),
            upcoming_expires_at=to_iso8601(now + self._cache_ttl),
            upcoming_items=fetched,
        )
        self._save_cache(next_cache)
        return fetched

    def _fetch_remote(self) -> List[Dict[str, Any]]:
        try:
            with httpx.Client(timeout=self._timeout_seconds) as client:
                resp = client.get(self._analysis_feed_url, headers={"Accept": "application/json"})
                resp.raise_for_status()
                payload = resp.json()
                if isinstance(payload, dict) and "items" in payload and isinstance(payload["items"], list):
                    return [x for x in payload["items"] if isinstance(x, dict)]
                if isinstance(payload, list):
                    return [x for x in payload if isinstance(x, dict)]
                return []
        except Exception:
            return []

    def _fetch_upcoming_remote(self, *, base: str) -> List[Dict[str, Any]]:
        url = f"{base}/api/analysis/{self._upcoming_sport}/upcoming?limit={self._upcoming_limit}"
        try:
            with httpx.Client(timeout=self._timeout_seconds) as client:
                resp = client.get(url, headers={"Accept": "application/json"})
                resp.raise_for_status()
                payload = resp.json()
                if isinstance(payload, list):
                    return [x for x in payload if isinstance(x, dict)]
                return []
        except Exception:
            return []

    def _load_cache(self) -> FeedCache:
        if not self._cache_path.exists():
            return FeedCache(
                fetched_at=None,
                expires_at=None,
                items=[],
                used_slugs={},
                upcoming_fetched_at=None,
                upcoming_expires_at=None,
                upcoming_items=[],
            )
        try:
            raw = json.loads(self._cache_path.read_text(encoding="utf-8") or "{}")
            return FeedCache(
                fetched_at=(raw.get("fetched_at") if isinstance(raw, dict) else None),
                expires_at=(raw.get("expires_at") if isinstance(raw, dict) else None),
                items=(raw.get("items") if isinstance(raw, dict) and isinstance(raw.get("items"), list) else []),
                used_slugs=(raw.get("used_slugs") if isinstance(raw, dict) and isinstance(raw.get("used_slugs"), dict) else {}),
                upcoming_fetched_at=(raw.get("upcoming_fetched_at") if isinstance(raw, dict) else None),
                upcoming_expires_at=(raw.get("upcoming_expires_at") if isinstance(raw, dict) else None),
                upcoming_items=(raw.get("upcoming_items") if isinstance(raw, dict) and isinstance(raw.get("upcoming_items"), list) else []),
            )
        except Exception:
            return FeedCache(
                fetched_at=None,
                expires_at=None,
                items=[],
                used_slugs={},
                upcoming_fetched_at=None,
                upcoming_expires_at=None,
                upcoming_items=[],
            )

    def _save_cache(self, cache: FeedCache) -> None:
        payload = {
            "fetched_at": cache.fetched_at,
            "expires_at": cache.expires_at,
            "items": cache.items,
            "used_slugs": cache.used_slugs,
            "upcoming_fetched_at": cache.upcoming_fetched_at,
            "upcoming_expires_at": cache.upcoming_expires_at,
            "upcoming_items": cache.upcoming_items,
        }
        self._cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _derive_base_from_feed_url(self) -> str:
        parsed = urlparse(self._analysis_feed_url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return ""

    def _build_used_slugs(self, *, now: datetime, posted_raw: List[dict]) -> Dict[str, datetime]:
        cache = self._load_cache()
        used: Dict[str, datetime] = {}
        for slug, ts in (cache.used_slugs or {}).items():
            try:
                used[str(slug)] = parse_iso8601(str(ts))
            except Exception:
                continue
        for rec in posted_raw:
            slug = str(rec.get("analysis_slug") or "").strip()
            if not slug:
                continue
            try:
                ts = parse_iso8601(str(rec.get("posted_at") or ""))
            except Exception:
                ts = now
            used[slug] = max(ts, used.get(slug, ts))
        return used

    def _mark_used(self, *, slug: str, now: datetime) -> None:
        cache = self._load_cache()
        cache.used_slugs[str(slug)] = to_iso8601(now)
        self._save_cache(cache)

    def _pick_variant(self, *, now: datetime, slug: str) -> str:
        idx = (hash(slug) ^ int(now.timestamp())) % len(self._ab_variants)
        return self._ab_variants[idx]


