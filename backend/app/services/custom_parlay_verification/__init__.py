"""Custom parlay automatic verification (server-side).

This package owns:
- Deterministic fingerprint generation (anti-abuse / idempotency key)
- Record creation + enqueue to the verification worker

User-facing terminology: "verification record" / "time-stamped confirmation".
"""


