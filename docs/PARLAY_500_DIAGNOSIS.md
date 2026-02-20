# Parlay Suggest 500 — Diagnosis

When **POST /api/parlay/suggest** returns **500 Internal Server Error**, the client sees a generic message. This doc explains causes and how to find the real error.

## What the user sees

- Browser: `Failed to load resource: the server responded with a status of 500`
- App: *"Server error occurred while generating parlay. Please try again in a moment."*

The frontend shows the backend `detail` when present; otherwise it shows that generic message.

## Where 500 can come from (backend)

All occur in `backend/app/api/routes/parlay.py` inside the `suggest_parlay` handler:

| Location | Cause | Backend detail (if set) |
|----------|--------|---------------------------|
| **Access check** | `check_parlay_access_with_purchase` throws (DB/Redis, bug) | `Failed to check parlay access: …` |
| **Parlay data invalid** | Builder returned wrong shape or missing keys | `Failed to generate parlay: Invalid parlay data structure` or `Missing required data fields: …` |
| **Response build** | `_prepare_parlay_response` throws (OpenAI, DB save, schema) | `Error building response: …` |
| **Non‑insufficient ValueError** | Builder raised ValueError that isn’t “not enough games” | The ValueError message |
| **Any other exception** | Unhandled exception in generation or fallback | Generic message; in **debug/development** the response includes `(debug: ErrorType: message)` |

## How to find the real error

1. **Backend logs**  
   Search for the request (e.g. by time or `trace_id` / `request_id`). The handler logs:
   - `"Access check failed: ..."` → access/DB/Redis issue
   - `"Error building parlay response: ..."` → `_prepare_parlay_response` (OpenAI, DB, Parlay model)
   - `"Parlay generation failed: ..."` with `traceback` in `extra` → uncaught exception in builder or route

2. **Development / debug**  
   With `DEBUG=true` or `ENVIRONMENT=development`, the 500 response body includes a short debug suffix, e.g.:
   - `detail`: `"... (debug: ValueError: some message)"`  
   The frontend will show this if the API returns it in `detail`.

3. **Log grep examples**
   ```bash
   # API logs (adjust unit name if different)
   journalctl -u parlaygorilla-api -n 500 | grep -E "parlay_suggest_failed|Error building parlay|Parlay generation failed|Access check failed"
   ```

## Common causes

- **DB/Redis** — connection or timeout during access check or parlay save
- **OpenAI** — disabled, key missing, or timeout in `ParlayExplanationManager.get_explanation`
- **Builder** — missing data (odds, games), bug in `ParlayBuilderService.build_parlay` or `MixedSportsParlayBuilder.build_mixed_parlay`
- **Schema/validation** — `ParlayResponse` or leg structure doesn’t match builder output (e.g. type or required field)

## Quick checks

- **OpenAI**: `OPENAI_ENABLED=true`, `OPENAI_API_KEY` set; try a simple OpenAI call from the same environment
- **DB**: Run a simple query and confirm connections
- **Redis**: Optional for suggest; if used for dedupe/telemetry, failures are swallowed (request still proceeds)

## See also

- `backend/app/api/routes/parlay.py` — `suggest_parlay` and `_prepare_parlay_response`
- `docs/OPS_RUNBOOK.md` — logs and service restart
