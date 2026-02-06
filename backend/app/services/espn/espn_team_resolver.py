"""ESPN team resolution by name with caching (no team_abbr required)."""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import httpx

from app.services.espn.espn_sport_resolver import EspnSportResolver
from app.services.team_name_normalizer import TeamNameNormalizer

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 86400  # 24 hours
REQUEST_TIMEOUT = 10.0


@dataclass
class ResolvedTeamRef:
    """Resolved ESPN team reference for fetching injuries."""

    team_id: Optional[str]
    injuries_url: Optional[str]
    team_url: Optional[str]
    matched_name: str
    match_method: str  # exact | normalized | fuzzy
    confidence: float  # 0..1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResolvedTeamRef":
        return cls(
            team_id=data.get("team_id"),
            injuries_url=data.get("injuries_url"),
            team_url=data.get("team_url"),
            matched_name=data.get("matched_name", ""),
            match_method=data.get("match_method", "unknown"),
            confidence=float(data.get("confidence", 0)),
        )


def _normalize_for_match(name: str) -> str:
    """Normalize team name for matching: lower, strip punctuation, collapse spaces."""
    s = (name or "").strip().lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _token_overlap_score(a: str, b: str) -> float:
    """Simple token overlap score in 0..1."""
    ta = set(_normalize_for_match(a).split())
    tb = set(_normalize_for_match(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


class EspnTeamResolver:
    """
    Resolve team name to ESPN team reference by fetching teams list and matching.
    Caches results 24h (Redis if configured, else in-memory TTL).
    """

    def __init__(
        self,
        *,
        cache_ttl_seconds: int = CACHE_TTL_SECONDS,
        timeout: float = REQUEST_TIMEOUT,
    ):
        self._cache_ttl = cache_ttl_seconds
        self._timeout = timeout
        self._normalizer = TeamNameNormalizer()
        self._memory_cache: Dict[str, tuple] = {}  # key -> (ResolvedTeamRef, expiry_ts)

    def _cache_key(self, sport: str, team_name: str) -> str:
        norm = _normalize_for_match(team_name)
        return f"espn:teamref:{sport.lower()}:{norm}"

    async def _get_cached(self, key: str) -> Optional[ResolvedTeamRef]:
        try:
            from app.services.redis.redis_client_provider import get_redis_provider
            provider = get_redis_provider()
            if provider.is_configured():
                client = provider.get_client()
                raw = await client.get(key.encode() if isinstance(key, str) else key)
                if raw:
                    data = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
                    return ResolvedTeamRef.from_dict(data)
        except Exception as e:
            logger.debug("ESPN team resolver Redis get failed: %s", e)
        if key in self._memory_cache:
            ref, expiry = self._memory_cache[key]
            if time.time() < expiry:
                return ref
            del self._memory_cache[key]
        return None

    async def _set_cached(self, key: str, ref: ResolvedTeamRef) -> None:
        payload = json.dumps(ref.to_dict())
        try:
            from app.services.redis.redis_client_provider import get_redis_provider
            provider = get_redis_provider()
            if provider.is_configured():
                client = provider.get_client()
                k = key.encode() if isinstance(key, str) else key
                await client.set(k, payload.encode(), ex=self._cache_ttl)
                return
        except Exception as e:
            logger.debug("ESPN team resolver Redis set failed: %s", e)
        self._memory_cache[key] = (ref, time.time() + self._cache_ttl)

    def _build_candidates(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build list of team candidates from ESPN API response."""
        teams = data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
        if teams:
            return [t.get("team", t) for t in teams]
        teams = data.get("teams", [])
        return [t.get("team", t) for t in teams]

    def _score_match(self, team_name: str, candidate: Dict[str, Any]) -> tuple[float, str]:
        """Return (confidence 0..1, match_method)."""
        norm_input = _normalize_for_match(team_name)
        display = (candidate.get("displayName") or "").strip()
        short = (candidate.get("shortDisplayName") or "").strip()
        name = (candidate.get("name") or "").strip()
        nickname = (candidate.get("nickname") or "").strip()
        abbr = (candidate.get("abbreviation") or "").strip()

        norm_display = _normalize_for_match(display)
        norm_short = _normalize_for_match(short)
        norm_name = _normalize_for_match(name)
        norm_nickname = _normalize_for_match(nickname)

        if norm_input == norm_display:
            return 1.0, "exact"
        if norm_input == norm_short or norm_input == norm_nickname:
            return 0.95, "normalized"
        if norm_input in norm_display or norm_display in norm_input:
            return 0.85, "contains"
        if norm_input in norm_short or norm_short in norm_input:
            return 0.85, "contains"
        best = 0.0
        for label, n in [(display, norm_display), (short, norm_short), (name, norm_name), (nickname, norm_nickname)]:
            if not n:
                continue
            score = _token_overlap_score(norm_input, n)
            if score > best:
                best = score
        if best >= 0.5:
            return min(0.75, best), "fuzzy"
        if abbr and norm_input == _normalize_for_match(abbr):
            return 0.9, "normalized"
        return 0.0, "none"

    def _ref_from_candidate(self, candidate: Dict[str, Any], base_url: str, confidence: float, method: str) -> ResolvedTeamRef:
        team_id = candidate.get("id")
        links = candidate.get("links", [])
        injuries_url = None
        team_url = None
        for link in links:
            if isinstance(link, dict):
                rel = (link.get("rel") or "").lower()
                href = (link.get("href") or "").strip()
                if "injuries" in rel and href:
                    injuries_url = href
                if "team" in rel and href:
                    team_url = href
        if not injuries_url and team_id:
            injuries_url = f"{base_url}/teams/{team_id}/injuries"
        matched = candidate.get("displayName") or candidate.get("shortDisplayName") or candidate.get("name") or ""
        return ResolvedTeamRef(
            team_id=str(team_id) if team_id is not None else None,
            injuries_url=injuries_url,
            team_url=team_url,
            matched_name=matched,
            match_method=method,
            confidence=confidence,
        )

    async def resolve_team_ref(self, sport: str, team_name: str) -> Optional[ResolvedTeamRef]:
        """
        Resolve team name to ESPN team reference. Uses cache (24h).
        Returns None if resolution fails; logs and optionally emits Telegram alert.
        """
        if not (team_name or "").strip():
            return None
        key = self._cache_key(sport, team_name)
        cached = await self._get_cached(key)
        if cached is not None:
            logger.info(
                "ESPN injuries resolved (cached)",
                extra={"sport": sport, "team_name": team_name, "match_method": cached.match_method, "confidence": cached.confidence},
            )
            return cached

        base_url = EspnSportResolver.get_base_url(sport)
        url = f"{base_url}/teams"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    logger.warning("ESPN teams list failed: %s %s", response.status_code, url)
                    await self._alert_resolve_failed(sport, team_name, f"http_{response.status_code}")
                    return None
                data = response.json()
        except Exception as e:
            logger.warning("ESPN team resolve failed: %s", e, extra={"sport": sport, "team_name": team_name})
            await self._alert_resolve_failed(sport, team_name, str(e))
            return None

        candidates = self._build_candidates(data)
        if not candidates:
            logger.warning("ESPN teams list empty: %s", url, extra={"sport": sport, "team_name": team_name})
            await self._alert_resolve_failed(sport, team_name, "empty_teams_list")
            return None

        best_ref = None
        best_score = 0.0
        best_method = "none"
        for c in candidates:
            score, method = self._score_match(team_name, c)
            if score > best_score:
                best_score = score
                best_method = method
                best_ref = self._ref_from_candidate(c, base_url, score, method)

        if best_ref is None or best_score < 0.5:
            logger.warning(
                "ESPN team resolve failed: no match",
                extra={"sport": sport, "team_name": team_name},
            )
            await self._alert_resolve_failed(sport, team_name, "no_match")
            return None

        await self._set_cached(key, best_ref)
        logger.info(
            "ESPN injuries resolved",
            extra={"sport": sport, "team_name": team_name, "match_method": best_ref.match_method, "confidence": best_ref.confidence},
        )
        return best_ref

    async def _alert_resolve_failed(self, sport: str, team_name: str, reason: str) -> None:
        """Emit optional Telegram alert when resolution fails."""
        try:
            from app.services.alerting import get_alerting_service
            await get_alerting_service().emit(
                event="injuries.espn_resolve_failed",
                severity="warning",
                payload={"sport": sport, "team_name": team_name, "reason": reason},
            )
        except Exception as e:
            logger.debug("Alert emit failed: %s", e)
