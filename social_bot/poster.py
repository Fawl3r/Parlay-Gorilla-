from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qsl, quote, urlparse
from uuid import uuid4

import httpx


def _pct(value: str) -> str:
    return quote(str(value), safe="~-._")


def _oauth_timestamp() -> str:
    return str(int(time.time()))


@dataclass(frozen=True)
class PublishResult:
    success: bool
    tweet_id: Optional[str] = None
    error: Optional[str] = None


class OAuth1Signer:
    def __init__(self, *, api_key: str, api_secret: str, access_token: str, access_secret: str) -> None:
        self._api_key = str(api_key or "")
        self._api_secret = str(api_secret or "")
        self._access_token = str(access_token or "")
        self._access_secret = str(access_secret or "")

    def auth_header(self, *, method: str, url: str) -> str:
        method_up = str(method).upper()
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        oauth_params = {
            "oauth_consumer_key": self._api_key,
            "oauth_nonce": secrets.token_hex(16),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": _oauth_timestamp(),
            "oauth_token": self._access_token,
            "oauth_version": "1.0",
        }

        # Signature params include oauth params + query params. JSON body params are NOT included.
        params: list[tuple[str, str]] = [(str(k), str(v)) for k, v in oauth_params.items()]
        for k, v in parse_qsl(parsed.query or "", keep_blank_values=True):
            params.append((str(k), str(v)))

        normalized = "&".join(f"{_pct(k)}={_pct(v)}" for k, v in sorted(params, key=lambda kv: (str(kv[0]), str(kv[1]))))
        base_string = "&".join([_pct(method_up), _pct(base_url), _pct(normalized)])
        signing_key = f"{_pct(self._api_secret)}&{_pct(self._access_secret)}"
        digest = hmac.new(signing_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1).digest()
        signature = base64.b64encode(digest).decode("utf-8")
        oauth_params["oauth_signature"] = signature

        header_params = ", ".join(f'{_pct(k)}=\"{_pct(v)}\"' for k, v in oauth_params.items())
        return f"OAuth {header_params}"


class XPoster:
    def __init__(
        self,
        *,
        dry_run: bool,
        api_base_url: str,
        bearer_token: str,
        oauth1: Optional[OAuth1Signer],
        timeout_seconds: float,
    ) -> None:
        self._dry_run = bool(dry_run)
        self._api_base_url = str(api_base_url or "https://api.x.com/2").rstrip("/")
        self._bearer = str(bearer_token or "").strip()
        self._oauth1 = oauth1
        self._timeout = float(timeout_seconds)

    def post(self, *, text: str, image_path: Optional[Path] = None) -> PublishResult:
        if self._dry_run:
            return PublishResult(success=True, tweet_id=f"dryrun-{uuid4()}")

        cleaned = str(text or "").strip()
        if not cleaned:
            return PublishResult(success=False, error="Empty post text")

        url = f"{self._api_base_url}/tweets"
        payload: dict = {"text": cleaned}

        # Try OAuth1 first (required for media), fallback to Bearer if 403 and Bearer available.
        use_oauth1 = self._oauth1 is not None
        use_bearer = bool(self._bearer) and not use_oauth1

        if not use_oauth1 and not use_bearer:
            return PublishResult(success=False, error="Missing X credentials (need X_BEARER_TOKEN or OAuth1 keys)")

        headers = {"Content-Type": "application/json"}
        if use_oauth1:
            headers["Authorization"] = self._oauth1.auth_header(method="POST", url=url)
        else:
            headers["Authorization"] = f"Bearer {self._bearer}"

        # Optional media attach. If upload fails, continue text-only (do not crash).
        if image_path and use_oauth1:
            media_id = self._upload_media(image_path=image_path)
            if media_id:
                payload["media"] = {"media_ids": [media_id]}

        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(url, headers=headers, content=json.dumps(payload).encode("utf-8"))
            if resp.status_code == 429:
                return PublishResult(success=False, error="Rate limited (429)")
            if resp.status_code == 403:
                error_text = resp.text[:300] if resp.text else ""
                if use_oauth1 and ("oauth1" in error_text.lower() or "permissions" in error_text.lower()):
                    # If OAuth1 fails with 403 and Bearer is available, suggest trying it.
                    if self._bearer:
                        return PublishResult(
                            success=False,
                            error="HTTP 403: OAuth1 missing write permissions. Either: (1) Fix OAuth1: https://developer.twitter.com → App → Settings → App permissions → 'Read and Write' → Regenerate tokens, OR (2) Use X_BEARER_TOKEN instead (set X_BEARER_TOKEN and remove OAuth1 keys).",
                        )
                    return PublishResult(
                        success=False,
                        error="HTTP 403: X app missing write permissions. Go to https://developer.twitter.com → Your App → Settings → User authentication settings → App permissions → Set to 'Read and Write'. Then regenerate your OAuth1 tokens.",
                    )
                return PublishResult(success=False, error=f"HTTP 403: {error_text}")
            if resp.status_code >= 400:
                return PublishResult(success=False, error=f"HTTP {resp.status_code}: {resp.text[:200]}")

            data = resp.json() or {}
            tweet_id = str((data.get("data") or {}).get("id") or "").strip()
            if not tweet_id:
                return PublishResult(success=False, error="Malformed X response (missing tweet id)")
            return PublishResult(success=True, tweet_id=tweet_id)
        except Exception as exc:
            return PublishResult(success=False, error=str(exc))

    def _upload_media(self, *, image_path: Path) -> Optional[str]:
        """
        Upload media via the v1.1 endpoint (requires OAuth1 user context).
        Returns media_id_string on success; None on any failure (soft-fail).
        """
        try:
            p = Path(image_path)
            if not p.exists() or not p.is_file():
                return None
            size = p.stat().st_size
            if size <= 0 or size > 8 * 1024 * 1024:
                return None
            ext = p.suffix.lower()
            if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
                return None
            data = p.read_bytes()
        except Exception:
            return None

        upload_url = "https://upload.twitter.com/1.1/media/upload.json"
        headers = {}
        if self._oauth1 is None:
            return None
        headers["Authorization"] = self._oauth1.auth_header(method="POST", url=upload_url)

        files = {"media": (p.name, data)}
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(upload_url, headers=headers, files=files)
            if resp.status_code >= 400:
                return None
            payload = resp.json() or {}
            media_id = str(payload.get("media_id_string") or payload.get("media_id") or "").strip()
            return media_id or None
        except Exception:
            return None


def build_oauth1_signer(
    *,
    api_key: str,
    api_secret: str,
    access_token: str,
    access_secret: str,
) -> Optional[OAuth1Signer]:
    if not (api_key and api_secret and access_token and access_secret):
        return None
    return OAuth1Signer(api_key=api_key, api_secret=api_secret, access_token=access_token, access_secret=access_secret)


