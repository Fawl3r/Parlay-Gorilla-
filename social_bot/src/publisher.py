from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx

from src.models import PublishResult


class PublisherError(RuntimeError):
    pass


def _utc_from_epoch_seconds(value: str) -> Optional[datetime]:
    try:
        return datetime.fromtimestamp(int(float(value)), tz=timezone.utc)
    except Exception:
        return None


class XPublisher:
    def __init__(
        self,
        *,
        api_base_url: str,
        bearer_token: str,
        media_upload_url: str,
        project_root: Optional[Path] = None,
        dry_run: bool,
        max_retries: int,
        backoff_initial_seconds: float,
        backoff_max_seconds: float,
        timeout_seconds: float,
    ) -> None:
        self._api_base_url = api_base_url.rstrip("/")
        self._bearer_token = bearer_token.strip()
        self._media_upload_url = (media_upload_url or "https://upload.x.com/1.1/media/upload.json").strip()
        self._project_root = project_root
        self._dry_run = bool(dry_run)
        self._max_retries = int(max_retries)
        self._backoff_initial = float(backoff_initial_seconds)
        self._backoff_max = float(backoff_max_seconds)
        self._timeout_seconds = float(timeout_seconds)
        self._pause_until: Optional[datetime] = None
        self._logger = logging.getLogger("social_bot")

    def publish_single(self, *, text: str, image_path: Optional[str] = None) -> PublishResult:
        payload: Dict[str, Any] = {"text": text}
        media_id = self._try_upload_media(image_path) if image_path else None
        if media_id:
            payload["media"] = {"media_ids": [media_id]}
        return self._publish_payload(payload)

    def publish_thread(self, *, tweets: List[str]) -> PublishResult:
        if not tweets:
            return PublishResult(success=False, tweet_ids=[], error="Empty thread")
        tweet_ids: List[str] = []
        in_reply_to: Optional[str] = None
        for tweet in tweets:
            payload: Dict[str, Any] = {"text": tweet}
            if in_reply_to:
                payload["reply"] = {"in_reply_to_tweet_id": in_reply_to}
            result = self._publish_payload(payload)
            if not result.success:
                return PublishResult(success=False, tweet_ids=tweet_ids, error=result.error, pause_until=result.pause_until)
            in_reply_to = result.tweet_ids[-1]
            tweet_ids.extend(result.tweet_ids)
        return PublishResult(success=True, tweet_ids=tweet_ids)

    def _publish_payload(self, payload: Dict[str, Any]) -> PublishResult:
        now = datetime.now(timezone.utc)
        if self._pause_until and now < self._pause_until:
            return PublishResult(success=False, tweet_ids=[], error="Rate limited (paused)", pause_until=self._pause_until)

        if self._dry_run:
            return PublishResult(success=True, tweet_ids=[f"dryrun-{uuid4()}"])

        if not self._bearer_token:
            return PublishResult(success=False, tweet_ids=[], error="Missing X bearer token")

        url = f"{self._api_base_url}/tweets"
        headers = {"Authorization": f"Bearer {self._bearer_token}", "Content-Type": "application/json"}

        for attempt in range(self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout_seconds) as client:
                    resp = client.post(url, headers=headers, json=payload)

                if resp.status_code == 429:
                    reset = _utc_from_epoch_seconds(resp.headers.get("x-rate-limit-reset", ""))
                    if reset:
                        self._pause_until = reset
                    return PublishResult(success=False, tweet_ids=[], error="Rate limited (429)", pause_until=reset)

                resp.raise_for_status()
                data = resp.json()
                tweet_id = str((data or {}).get("data", {}).get("id") or "").strip()
                if not tweet_id:
                    return PublishResult(success=False, tweet_ids=[], error="Malformed X response (missing tweet id)")
                return PublishResult(success=True, tweet_ids=[tweet_id])

            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code if exc.response else 0
                if 500 <= code < 600 and attempt < self._max_retries:
                    self._sleep_backoff(attempt)
                    continue
                return PublishResult(success=False, tweet_ids=[], error=f"HTTP {code}")
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt < self._max_retries:
                    self._sleep_backoff(attempt)
                    continue
                return PublishResult(success=False, tweet_ids=[], error="Network/timeout")
            except Exception as exc:
                return PublishResult(success=False, tweet_ids=[], error=str(exc))

        return PublishResult(success=False, tweet_ids=[], error="Exhausted retries")

    def _sleep_backoff(self, attempt: int) -> None:
        delay = min(self._backoff_max, self._backoff_initial * (2**attempt))
        time.sleep(max(0.0, delay))

    def _try_upload_media(self, image_path: Optional[str]) -> Optional[str]:
        if not image_path:
            return None
        if self._dry_run:
            return None
        if not self._bearer_token:
            return None

        resolved = self._resolve_media_path(image_path)
        if not resolved.exists():
            self._logger.warning("Media upload skipped; missing file: %s", resolved)
            return None

        headers = {"Authorization": f"Bearer {self._bearer_token}"}
        try:
            with resolved.open("rb") as f:
                files = {"media": (resolved.name, f, "image/png")}
                with httpx.Client(timeout=self._timeout_seconds) as client:
                    resp = client.post(self._media_upload_url, headers=headers, files=files)
            if resp.status_code == 429:
                self._logger.warning("Media upload rate limited (429); posting text-only.")
                return None
            resp.raise_for_status()
            data = resp.json() or {}
            media_id = str(data.get("media_id_string") or data.get("media_id") or "").strip()
            if not media_id:
                self._logger.warning("Media upload returned malformed response; posting text-only.")
                return None
            return media_id
        except Exception as exc:
            self._logger.warning("Media upload failed; posting text-only. error=%s", str(exc))
            return None

    def _resolve_media_path(self, image_path: str) -> Path:
        p = Path(str(image_path))
        if p.is_absolute():
            return p
        base = self._project_root or Path.cwd()
        return base / p


