# Parlay Gorilla Content Engine (Air-Gapped)

This directory contains the content-only system for Parlay Gorilla. It is fully isolated from the application and only reads/writes files inside `/content_engine/`.

## Quickstart

From the `content_engine` folder:

1) Create and activate a virtual environment (optional but recommended).
2) Install dependencies:

```
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3) Validate or approve content:

```
python -m pg_content_engine x validate
python -m pg_content_engine x approve
python -m pg_content_engine video validate
python -m pg_content_engine video approve
```

Use `--keep` to keep items in the queue after approval:

```
python -m pg_content_engine x approve --keep
```

## Air-Gapped Guarantee

- Only `/content_engine/` is touched.
- No application code is read or modified.
- The publisher bot reads only `outputs/approved.json` and writes `outputs/post_log.json`.

## Operating Procedure

1) Draft new items into:
   - `outputs/queue.json` for X items
   - `outputs/video_queue.json` for video scripts
2) Run `validate` to see issues without modifying files.
3) Run `approve` to move items into approved/rejected outputs.
4) Publisher bot reads `outputs/approved.json` only.

## File Outputs

- `outputs/queue.json`: pending X items
- `outputs/approved.json`: approved X items
- `outputs/rejected.json`: rejected X items + `rejection_reasons`
- `outputs/post_log.json`: publisher log output
- `outputs/video_queue.json`: pending video scripts
- `outputs/video_approved.json`: approved video scripts
- `outputs/video_rejected.json`: rejected video scripts + `rejection_reasons`

## JSON Contracts

### X item (valid)

```
{
  "id": "pg_x_014",
  "type": "post",
  "topic": "why parlays fail",
  "text": "Most parlays do not lose because of bad luck. They lose because people stack games without understanding matchups.",
  "style_tag": "mistake_breakdown",
  "compliance": {
    "no_guarantees": true,
    "no_hype": true,
    "no_emojis": true
  },
  "hashtags": [],
  "schedule": {
    "priority": "normal",
    "window": "evening",
    "cadence": "daily",
    "evergreen": true,
    "expiration_hours": null
  },
  "status": "pending"
}
```

### X item (invalid)

```
{
  "id": "pg_x_bad",
  "type": "post",
  "topic": "discipline",
  "text": "This will win. Free money.",
  "style_tag": "authority",
  "compliance": {
    "no_guarantees": true,
    "no_hype": false,
    "no_emojis": true
  },
  "hashtags": ["#Parlay"],
  "schedule": {
    "priority": "normal",
    "window": "evening",
    "cadence": "daily",
    "evergreen": true,
    "expiration_hours": 24
  },
  "status": "pending"
}
```

### Video item (valid)

```
{
  "id": "pg_v_014",
  "type": "video_script",
  "topic": "risk management",
  "script": "Discipline is not a mood. It is the standard you keep when variance shows up. If the leg does not have a clean edge, you cut it. That is how you keep risk controlled and avoid chasing noise.",
  "format_tag": "discipline_reminder",
  "compliance": {
    "no_guarantees": true,
    "no_hype": true,
    "no_emojis": true
  },
  "schedule": {
    "priority": "normal",
    "window": "evening",
    "cadence": "daily",
    "evergreen": true,
    "expiration_hours": null
  },
  "status": "pending"
}
```

### Video item (invalid)

```
{
  "id": "pg_v_bad",
  "type": "video_script",
  "topic": "discipline",
  "script": "Free money. Bet now.",
  "format_tag": "discipline_reminder",
  "compliance": {
    "no_guarantees": true,
    "no_hype": true,
    "no_emojis": true
  },
  "schedule": {
    "priority": "normal",
    "window": "evening",
    "cadence": "daily",
    "evergreen": true,
    "expiration_hours": null
  },
  "status": "pending"
}
```

## Validation Rules (Highlights)

- No emojis or ALL CAPS emphasis.
- No banned phrases or outcome certainty.
- Max 2 hashtags, and they must match the text.
- X text blocks must be 280 characters or fewer.
- Video scripts must be 15–30 seconds (word-count heuristic).
- Schedule metadata must be valid and consistent.
