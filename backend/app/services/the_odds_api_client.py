"""HTTP client for The Odds API (v4) with key fallback and safe retries.

Implements:
- Current odds: /v4/sports/{sport}/odds
- Historical odds: /v4/historical/sports/{sport}/odds
- Historical event odds: /v4/historical/sports/{sport}/events/{eventId}/odds

Docs:
- https://the-odds-api.com/liveapi/guides/v4/#get-historical-odds
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import httpx


@dataclass(frozen=True)
class OddsApiKeys:
    primary: str
    fallback: Optional[str] = None

    def iter_keys(self) -> Iterable[str]:
        keys = [k for k in [self.primary, self.fallback] if k]
        seen: set[str] = set()
        for k in keys:
            if k in seen:
                continue
            seen.add(k)
            yield k


class TheOddsApiClient:
    BASE_URL = "https://api.the-odds-api.com/v4"

    def __init__(self, *, api_keys: OddsApiKeys):
        self._keys = api_keys

    async def get_current_odds(
        self,
        *,
        sport_key: str,
        regions: str,
        markets: str,
        odds_format: str = "american",
        timeout_seconds: float = 15.0,
    ) -> List[dict]:
        url = f"{self.BASE_URL}/sports/{sport_key}/odds"
        return await self._get_with_fallback(
            url=url,
            params={
                "regions": regions,
                "markets": markets,
                "oddsFormat": odds_format,
            },
            timeout_seconds=timeout_seconds,
        )

    async def get_sports(self, *, timeout_seconds: float = 10.0) -> List[dict]:
        """
        Return The Odds API sports list (includes `active` flag).

        Docs: https://the-odds-api.com/liveapi/guides/v4/#get-sports
        """
        url = f"{self.BASE_URL}/sports"
        data = await self._get_with_fallback(url=url, params={}, timeout_seconds=timeout_seconds)
        if not isinstance(data, list):
            return []
        # Ensure list of dicts
        return [x for x in data if isinstance(x, dict)]

    async def get_historical_odds(
        self,
        *,
        sport_key: str,
        date_iso: str,
        regions: str,
        markets: str,
        odds_format: str = "american",
        timeout_seconds: float = 20.0,
    ) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/historical/sports/{sport_key}/odds"
        return await self._get_with_fallback(
            url=url,
            params={
                "date": date_iso,
                "regions": regions,
                "markets": markets,
                "oddsFormat": odds_format,
            },
            timeout_seconds=timeout_seconds,
        )

    async def get_historical_event_odds(
        self,
        *,
        sport_key: str,
        event_id: str,
        date_iso: str,
        regions: str,
        markets: str,
        odds_format: str = "american",
        timeout_seconds: float = 20.0,
    ) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/historical/sports/{sport_key}/events/{event_id}/odds"
        return await self._get_with_fallback(
            url=url,
            params={
                "date": date_iso,
                "regions": regions,
                "markets": markets,
                "oddsFormat": odds_format,
            },
            timeout_seconds=timeout_seconds,
        )

    async def _get_with_fallback(
        self,
        *,
        url: str,
        params: Dict[str, Any],
        timeout_seconds: float,
    ) -> Any:
        last_error: Optional[Exception] = None

        for api_key in self._keys.iter_keys():
            try:
                return await self._get_once(
                    url=url,
                    params={**params, "apiKey": api_key},
                    timeout_seconds=timeout_seconds,
                )
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status = exc.response.status_code
                # Only fallback on auth/quota-type errors.
                if status in (401, 403):
                    continue
                raise
            except Exception as exc:
                last_error = exc
                continue

        raise last_error or RuntimeError("The Odds API request failed")

    @staticmethod
    async def _get_once(*, url: str, params: Dict[str, Any], timeout_seconds: float) -> Any:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
            # Retry once on 429 (burst protection) with a short delay.
            for attempt in range(2):
                resp = await client.get(url, params=params)
                if resp.status_code == 429 and attempt == 0:
                    await _sleep_seconds(1.0)
                    continue
                resp.raise_for_status()
                return resp.json()


async def _sleep_seconds(seconds: float) -> None:
    # Local helper to avoid importing asyncio in every module.
    import asyncio

    await asyncio.sleep(max(0.0, float(seconds)))


