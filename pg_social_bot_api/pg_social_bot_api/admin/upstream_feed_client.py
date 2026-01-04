from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional
from urllib.parse import urlparse, urlunparse

import httpx


@dataclass(frozen=True)
class UpstreamAnalysisItem:
    slug: str
    angle: str
    key_points: List[str]
    risk_note: Optional[str]
    cta_url: str
    published_at: Optional[str]


class UpstreamFeedClient:
    def __init__(self, *, url: str, timeout_seconds: float = 10.0, production_frontend_url: Optional[str] = None) -> None:
        self._url = (url or "").strip()
        self._timeout = float(timeout_seconds)
        self._production_frontend_url = (production_frontend_url or "").strip().rstrip("/")

    async def fetch(self) -> List[UpstreamAnalysisItem]:
        if not self._url:
            raise ValueError("Upstream analysis feed URL is not configured. Set UPSTREAM_ANALYSIS_FEED_URL in environment variables.")
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(self._url)
                resp.raise_for_status()
                payload = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(
                    f"Analysis feed endpoint not found at {self._url}. "
                    "Please verify the URL is correct and the upstream service is running."
                ) from e
            raise ValueError(
                f"Failed to fetch analysis feed from {self._url}: HTTP {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            raise ValueError(
                f"Failed to connect to analysis feed at {self._url}. "
                "Please verify the service is running and the URL is correct."
            ) from e
        items_raw = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items_raw, list):
            return []
        out: List[UpstreamAnalysisItem] = []
        for raw in items_raw:
            if not isinstance(raw, dict):
                continue
            slug = str(raw.get("slug") or "").strip()
            if not slug:
                continue
            key_points_raw = raw.get("key_points") or []
            key_points = [str(x).strip() for x in key_points_raw if str(x).strip()] if isinstance(key_points_raw, list) else []
            
            # Transform CTA URL: replace localhost URLs with production URL if configured
            cta_url_raw = str(raw.get("cta_url") or "").strip()
            cta_url = self._transform_cta_url(cta_url_raw)
            
            out.append(
                UpstreamAnalysisItem(
                    slug=slug,
                    angle=str(raw.get("angle") or "").strip(),
                    key_points=key_points[:5],
                    risk_note=(str(raw.get("risk_note")).strip() if raw.get("risk_note") else None),
                    cta_url=cta_url,
                    published_at=(str(raw.get("generated_at") or "").strip() or None),
                )
            )
        return out
    
    def _transform_cta_url(self, url: str) -> str:
        """Transform localhost CTA URLs to production URLs if production URL is configured."""
        if not url or not self._production_frontend_url:
            return url
        
        try:
            parsed = urlparse(url)
            # Check if URL contains localhost (any port)
            if parsed.hostname in ("localhost", "127.0.0.1") or (parsed.hostname and "localhost" in parsed.hostname.lower()):
                # Replace with production frontend URL, preserving path and query
                production_parsed = urlparse(self._production_frontend_url)
                new_url = urlunparse((
                    production_parsed.scheme or "https",
                    production_parsed.netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
                return new_url
        except Exception:
            # If URL parsing fails, return original
            pass
        
        return url


