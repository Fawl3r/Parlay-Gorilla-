from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional, Sequence

from app.services.saved_parlays.hashing import CanonicalJsonSerializer, Sha256HexHasher, canonical_json, sha256_hex


@dataclass(frozen=True)
class CustomParlayFingerprintLeg:
    """
    Minimal, deterministic leg snapshot for anti-abuse fingerprinting.

    Notes:
    - Include `pick` + `point` to avoid collisions (e.g., O/U with same odds).
    - Include `odds_snapshot` to ensure different price snapshots produce different fingerprints.
    """

    matchup_id: str
    market_type: str
    pick: str
    odds_snapshot: str
    point: Optional[float] = None
    market_id: Optional[str] = None


@dataclass(frozen=True)
class CustomParlayFingerprintResult:
    parlay_fingerprint: str
    generation_window_start_epoch_seconds: int


def _epoch_seconds(dt: datetime) -> int:
    if dt.tzinfo is None:
        # Treat naive datetimes as UTC by convention.
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.astimezone(timezone.utc).timestamp())


def _bucket_start(epoch_seconds: int, window_seconds: int) -> int:
    w = max(1, int(window_seconds))
    return int(epoch_seconds // w) * w


def _normalize_str(value: str) -> str:
    return str(value or "").strip()


class CustomParlayFingerprintGenerator:
    """
    Deterministic fingerprint generator for Custom AI parlay verification.

    The fingerprint is used as:
    - The DB-level idempotency key (unique constraint)
    - The proof-layer hash input (hash-only, no PII leaked on-chain)
    """

    def __init__(
        self,
        *,
        model_version: str,
        window_seconds: int,
        serializer: Optional[CanonicalJsonSerializer] = None,
        hasher: Optional[Sha256HexHasher] = None,
    ):
        self._model_version = _normalize_str(model_version)
        self._window_seconds = max(60, int(window_seconds))  # prevent overly-small buckets
        self._serializer = serializer or canonical_json
        self._hasher = hasher or sha256_hex

    def compute(
        self,
        *,
        user_id: str,
        legs: Sequence[CustomParlayFingerprintLeg],
        now_utc: Optional[datetime] = None,
    ) -> CustomParlayFingerprintResult:
        now = now_utc or datetime.now(timezone.utc)
        window_start = _bucket_start(_epoch_seconds(now), self._window_seconds)

        normalized_legs = self._normalize_and_sort_legs(legs)
        payload = {
            "v": 1,
            "user_id": _normalize_str(user_id),
            "model_version": self._model_version,
            "generation_window": int(window_start),
            "legs": [
                {
                    "matchup_id": leg.matchup_id,
                    "market_type": leg.market_type,
                    "pick": leg.pick,
                    "point": leg.point,
                    "odds_snapshot": leg.odds_snapshot,
                    "market_id": leg.market_id,
                }
                for leg in normalized_legs
            ],
        }

        payload_str = self._serializer.serialize(payload)
        digest = self._hasher.hash_text(payload_str)

        return CustomParlayFingerprintResult(
            parlay_fingerprint=str(digest),
            generation_window_start_epoch_seconds=int(window_start),
        )

    @staticmethod
    def _normalize_and_sort_legs(legs: Iterable[CustomParlayFingerprintLeg]) -> list[CustomParlayFingerprintLeg]:
        out: list[CustomParlayFingerprintLeg] = []
        for leg in legs:
            out.append(
                CustomParlayFingerprintLeg(
                    matchup_id=_normalize_str(leg.matchup_id),
                    market_type=_normalize_str(leg.market_type).lower(),
                    pick=_normalize_str(leg.pick).lower(),
                    odds_snapshot=_normalize_str(leg.odds_snapshot),
                    point=float(leg.point) if leg.point is not None else None,
                    market_id=_normalize_str(leg.market_id) if leg.market_id else None,
                )
            )

        # Deterministic order (anti hash-churn).
        out.sort(
            key=lambda l: (
                l.matchup_id,
                l.market_type,
                l.pick,
                "" if l.point is None else f"{l.point:.6g}",
                l.market_id or "",
                l.odds_snapshot,
            )
        )
        return out


