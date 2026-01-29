"""
Structured event logging: one event name + compact JSON payload.
Machine-parseable for log aggregation; include trace_id when available (request.state.request_id).
"""

import json
import logging
from typing import Any, Optional


def _serialize(value: Any) -> Any:
    """Convert non-JSON-serializable values for compact output."""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "__dict__") and not isinstance(value, (dict, list, str, int, float, bool, type(None))):
        return str(value)
    return value


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    trace_id: Optional[str] = None,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    """
    Emit a structured event: event name + compact JSON payload.

    Use trace_id from request.state.request_id when in request context.
    """
    payload = {"event": event}
    if trace_id is not None:
        payload["trace_id"] = trace_id
    for k, v in fields.items():
        if v is None:
            continue
        try:
            payload[k] = _serialize(v)
        except Exception:
            payload[k] = str(v)
    message = json.dumps(payload, default=str, separators=(",", ":"))
    logger.log(level, message)
