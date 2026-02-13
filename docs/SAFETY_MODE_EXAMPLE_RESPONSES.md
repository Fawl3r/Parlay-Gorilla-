# Safety Mode — Example JSON (local)

Actual output from `backend/scripts/safety_mode_examples.py` (or from calling the API locally).

---

## GET /ops/safety (local)

### GREEN (default, no triggers)

```json
{
  "state": "GREEN",
  "reasons": [],
  "telemetry": {
    "daily_api_budget": 100
  },
  "safety_mode_enabled": true
}
```

### YELLOW (forced by stale refresh — set last_successful_* to old timestamp)

```json
{
  "state": "YELLOW",
  "reasons": [
    "odds_data_stale",
    "games_data_stale"
  ],
  "telemetry": {
    "last_successful_odds_refresh_at": 1.0,
    "last_successful_games_refresh_at": 1.0,
    "daily_api_budget": 100
  },
  "safety_mode_enabled": true
}
```

### RED (forced by error_count_5m >= threshold, e.g. 30 >= 25)

```json
{
  "state": "RED",
  "reasons": [
    "error_count_5m=30 >= 25"
  ],
  "telemetry": {
    "last_successful_odds_refresh_at": 1.0,
    "last_successful_games_refresh_at": 1.0,
    "error_count_5m": 30,
    "daily_api_budget": 100
  },
  "safety_mode_enabled": true
}
```

---

## Parlay generation responses (POST /api/parlay/suggest)

### GREEN (200)

Normal `ParlayResponse` only. No safety fields (or `safety_mode`, `warning`, `reasons` are null/absent).

Example shape (excerpt):

```json
{
  "id": "...",
  "legs": [...],
  "num_legs": 5,
  "parlay_hit_prob": 0.42,
  "overall_confidence": 0.65,
  "ai_summary": "...",
  "ai_risk_notes": "...",
  "confidence_scores": [0.7, 0.6, ...],
  "safety_mode": null,
  "warning": null,
  "reasons": null
}
```

### YELLOW (200)

Same as GREEN plus degraded-mode fields; `num_legs` may be capped to `SAFETY_MODE_YELLOW_MAX_LEGS` (e.g. 4).

```json
{
  "id": "...",
  "legs": [...],
  "num_legs": 4,
  "parlay_hit_prob": 0.38,
  "overall_confidence": 0.62,
  "ai_summary": "...",
  "ai_risk_notes": "...",
  "safety_mode": "YELLOW",
  "warning": "Limited data mode.",
  "reasons": [
    "odds_data_stale",
    "games_data_stale"
  ]
}
```

### RED (503)

Generation is blocked. No parlay built; body is only:

```json
{
  "safety_mode": "RED",
  "message": "Parlay generation temporarily paused for data reliability. Try again soon.",
  "reasons": [
    "error_count_5m=30 >= 25"
  ]
}
```

---

To regenerate these locally:

```bash
cd backend
python scripts/safety_mode_examples.py
```
