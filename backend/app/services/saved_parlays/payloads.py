"""Canonical hash payload builders for Saved Parlays."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.services.saved_parlays.hashing import canonical_json, sha256_hex


SCHEMA_VERSION = "pg_parlay_v2"


@dataclass(frozen=True)
class SavedParlayHashInputs:
    saved_parlay_id: str
    account_number: str
    created_at_utc: datetime
    parlay_type: str
    legs: List[Dict[str, Any]]
    app_version: str


class SavedParlayHashPayloadBuilder:
    """Builds deterministic payloads and hashes for saved parlays."""

    def build_payload(self, inputs: SavedParlayHashInputs) -> Dict[str, Any]:
        created_at = inputs.created_at_utc
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        # Canonicalize legs ordering: sorting prevents “selection order” hash churn.
        legs_sorted = sorted(inputs.legs, key=self._leg_sort_key)

        return {
            "schema_version": SCHEMA_VERSION,
            "app_version": inputs.app_version,
            "parlay_id": inputs.saved_parlay_id,
            "account_number": inputs.account_number,
            "created_at_utc": created_at.astimezone(timezone.utc).isoformat(),
            "parlay_type": inputs.parlay_type,
            "legs": legs_sorted,
        }

    def compute_content_hash(self, inputs: SavedParlayHashInputs) -> str:
        payload = self.build_payload(inputs)
        payload_str = canonical_json.serialize(payload)
        return sha256_hex.hash_text(payload_str)

    def _leg_sort_key(self, leg: Dict[str, Any]) -> str:
        # Stable sort key; missing keys collapse to empty strings.
        game_id = str(leg.get("game_id") or "")
        market_type = str(leg.get("market_type") or "")
        pick = str(leg.get("pick") or leg.get("outcome") or "")
        market_id = str(leg.get("market_id") or "")
        odds = str(leg.get("odds") or "")
        point = str(leg.get("point") or "")
        return "|".join([game_id, market_type, pick, market_id, odds, point])


payload_builder = SavedParlayHashPayloadBuilder()


