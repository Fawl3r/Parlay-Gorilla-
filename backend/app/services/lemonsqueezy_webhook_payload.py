"""
Helpers for parsing LemonSqueezy webhook payloads.

Why this exists:
- LemonSqueezy "custom data" can appear in multiple places depending on event type.
- We want a single, well-tested place to extract that custom data consistently.
- For idempotency, we need a stable event key for duplicate deliveries even when the
  provider doesn't supply a unique event id field.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


def _is_blank(value: object) -> bool:
    return value is None or value == "" or value == {} or value == []  # type: ignore[comparison-overlap]


def _parse_json_object_maybe(value: object) -> dict[str, Any]:
    """
    Parse a JSON object from either:
    - dict (returned as-is)
    - str (attempt json.loads)
    Otherwise returns {}.
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


@dataclass(frozen=True)
class LemonSqueezyWebhookPayload:
    raw_body: bytes
    payload: dict[str, Any]

    def event_name(self) -> str:
        meta = self.payload.get("meta", {}) or {}
        return str(meta.get("event_name") or "unknown")

    def idempotency_key(self) -> str:
        """
        Stable id for deduping identical webhook deliveries.

        LemonSqueezy payloads don't reliably include a universally unique event id
        across all event types, so we fall back to hashing the raw request body.
        """
        meta = self.payload.get("meta", {}) or {}
        # Prefer explicit event identifiers if present.
        for key in ("event_id", "id", "request_id"):
            candidate = meta.get(key)
            candidate_str = str(candidate).strip() if candidate is not None else ""
            if candidate_str:
                return candidate_str
        return f"sha256:{hashlib.sha256(self.raw_body).hexdigest()}"

    def data_id(self) -> str:
        data = self.payload.get("data", {}) or {}
        return str(data.get("id") or "").strip()

    def data_type(self) -> str:
        data = self.payload.get("data", {}) or {}
        return str(data.get("type") or "").strip()

    def attributes(self) -> dict[str, Any]:
        data = self.payload.get("data", {}) or {}
        attrs = data.get("attributes", {}) or {}
        return attrs if isinstance(attrs, dict) else {}

    def custom_data(self) -> dict[str, Any]:
        """
        Extract custom data for both subscription and order events.

        We merge values from several possible locations and keep the first
        non-blank value for each key.
        """
        attrs = self.attributes()
        meta = self.payload.get("meta", {}) or {}

        merged: dict[str, Any] = {}

        def merge(source: dict[str, Any]) -> None:
            for k, v in (source or {}).items():
                if _is_blank(v):
                    continue
                if _is_blank(merged.get(k)):
                    merged[k] = v

        # 1) meta.custom_data (commonly used when setting checkout_data.custom)
        meta_custom = meta.get("custom_data")
        merge(meta_custom if isinstance(meta_custom, dict) else {})

        # 2) attributes.custom (often JSON string for one-time orders)
        merge(_parse_json_object_maybe(attrs.get("custom")))

        # 3) attributes.checkout_data.custom (defensive: some payloads include this)
        checkout_data = attrs.get("checkout_data")
        if isinstance(checkout_data, dict):
            merge(_parse_json_object_maybe(checkout_data.get("custom")))

        # 4) subscription item custom_data
        first_item = attrs.get("first_subscription_item")
        if isinstance(first_item, dict):
            item_custom = first_item.get("custom_data")
            merge(item_custom if isinstance(item_custom, dict) else {})

        # 5) order items custom_data (some order payloads store custom data per item)
        order_items = attrs.get("order_items")
        if isinstance(order_items, dict):
            items = order_items.get("data", []) or []
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    item_attrs = item.get("attributes", {}) or {}
                    if not isinstance(item_attrs, dict):
                        continue
                    merge(_parse_json_object_maybe(item_attrs.get("custom_data")))
                    merge(_parse_json_object_maybe(item_attrs.get("custom")))

        return merged


