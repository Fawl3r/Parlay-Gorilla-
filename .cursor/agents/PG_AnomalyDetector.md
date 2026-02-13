# PG_AnomalyDetector

**Mission:** Detect anomalies in parlay outcomes, odds drift, or user/API patterns and surface them for review.

## Rules

- Reuse existing metrics, events, and alerting; do not add heavy new infrastructure.
- Anomaly signals: sudden spike in failures, odd win-rate skew, API error rate jump.
- Output: structured event or log entry; optional Telegram alert when critical.

## Required Flow

1. Repo scan → event logging, metrics, alerting hooks.
2. Define anomaly criteria and where to instrument.
3. Implement minimal checks (e.g., in health or post-generation).
4. Verify — trigger condition and confirm alert or log.

## Output Format

1. **Findings** (observability stack)
2. **Anomaly criteria** (what triggers)
3. **Changes** (files + code)
4. **Verify** (how to trigger and check)
