# SUI Verifier Worker (Pattern A)

This document describes the always-on SUI verification worker used on OCI (and optionally elsewhere) when verification is delivered via the DB instead of Redis.

**Production deployment:** On Oracle Cloud, the **Oracle VM is the only verification worker**. The Render verification worker is disabled; verification runs solely via the `verifier` service on the VM with `VERIFICATION_DELIVERY=db`. Do not run a Redis-based verification worker against the same DB as the Oracle verifier.

## How it works

- **Pattern A**: DB-polling. The worker runs in an infinite loop and, every N seconds (configurable via `VERIFIER_POLL_INTERVAL_SEC`, default 15):
  1. Optionally releases stuck records: any `processing` row with `processing_started_at` older than 15 minutes is set back to `queued`.
  2. Atomically claims one row: `UPDATE verification_records SET status = 'processing', processing_started_at = now() WHERE id = (SELECT id FROM verification_records WHERE status = 'queued' ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED) RETURNING ...`.
  3. Calls the SUI chain to create the proof (same Move contract as the legacy TS worker: `create_proof(data_hash, created_at)`).
  4. On success: sets the record to `confirmed` with `tx_digest` and `object_id`.
  5. On failure: sets the record to `failed` and stores the error message.

- **Idempotent / restart-safe**: Only `queued` rows are claimed; `confirmed` and `failed` are left alone. If the process crashes while a row is `processing`, the timeout release (step 1) will eventually set it back to `queued` so it can be retried.

- **Structured logging**: Each verification logs `record_id`, `parlay_id` (saved_parlay_id), `tx_hash`, `verification_result`, `duration_ms`.

- **Heartbeat**: The worker logs “verifier alive” every `VERIFIER_HEARTBEAT_INTERVAL_SEC` (default 60) when it has nothing to process.

- **Backoff + jitter**: On DB or SUI errors, the worker backs off exponentially (with jitter) before the next cycle.

## Confirming only one verifier is running

On OCI we run a single VM and a single `docker compose -f docker-compose.prod.yml` stack with one `verifier` service. So only one verifier process should be running. To confirm:

- `docker compose -f docker-compose.prod.yml ps` — you should see one `parlaygorilla-verifier` container.
- `docker compose -f docker-compose.prod.yml logs verifier` — logs from that single process.

Do not run multiple stacks or multiple verifier containers against the same DB without coordination (e.g. leader election); the current design assumes a single verifier.

## Disabling the Render worker during cutover

Oracle VM is the single source of truth for verification. Before or when switching to the OCI verifier:

1. In the Render dashboard, pause or delete the **parlay-gorilla-verification-worker** service so it no longer consumes from Redis.
2. Set `VERIFICATION_DELIVERY=db` on the API (on OCI) so new verification records are only written to the DB and not pushed to Redis.
3. The OCI verifier is then the only consumer of `queued` records; keep the Render worker disabled.

## Reading verifier logs

On the Oracle VM (or wherever the stack runs):

```bash
cd /opt/parlaygorilla
docker compose -f docker-compose.prod.yml logs -f verifier
```

For a one-off tail:

```bash
docker compose -f docker-compose.prod.yml logs --tail=100 verifier
```

## Environment variables (verifier)

- `DATABASE_URL`: PostgreSQL connection string (sync; postgresql:// or postgres://).
- `SUI_RPC_URL`, `SUI_PRIVATE_KEY`, `SUI_PACKAGE_ID`: Required for SUI proof creation.
- `SUI_MODULE` (default `parlay_proof`), `SUI_FUNCTION` (default `create_proof`): Move contract.
- `VERIFIER_POLL_INTERVAL_SEC` (default 15): Seconds between poll cycles.
- `VERIFIER_HEARTBEAT_INTERVAL_SEC` (default 60): Seconds between “verifier alive” logs when idle.
- `VERIFIER_PROCESSING_TIMEOUT_SEC` (default 900): After this many seconds, a row left in `processing` is released back to `queued`.
- `VERIFICATION_MAX_ATTEMPTS`: Used in retry logic; see worker code.
- `SUI_GAS_BUDGET`: Optional; passed to the SUI proof client.

## Optional: heartbeat table

The worker does not currently write to a DB heartbeat table. If you want DB-based liveness checks, add a small table and have the verifier update a row every N seconds; the current design relies on log-based “verifier alive” and process/container health.

---

## Recovery: requeuing failed records (enqueue-only failures)

If records failed only because **enqueue to Redis** failed (e.g. "Enqueue failed: ResponseError" before switching to Oracle/DB delivery), they are still valid candidates for verification. The Oracle verifier only reads from the DB, so you can safely move them back to `queued` so the verifier will pick them up.

### 1. Identify eligible records

Eligible records are those that:

- Have `status = 'failed'`
- Have an error message that indicates **only** an enqueue/Redis failure (e.g. `Enqueue failed: ResponseError`, or similar wording from your queue client)
- Do **not** have a chain receipt yet (no successful verification attempt)

In SQL (run against your production DB with appropriate safeguards):

```sql
-- Inspect only; no writes yet
SELECT id, user_id, saved_parlay_id, status, error, tx_digest, created_at
FROM verification_records
WHERE status = 'failed'
  AND (error ILIKE '%enqueue%' OR error ILIKE '%redis%' OR error ILIKE '%ResponseError%')
  AND tx_digest IS NULL
ORDER BY created_at DESC
LIMIT 100;
```

Confirm the `error` values are indeed enqueue/Redis-related and not chain or business-logic failures.

### 2. Requeue safely (set failed → queued)

For each eligible record you want to retry:

- Set `status = 'queued'`
- Clear `error` (set to `NULL`) so the verifier and UI don't show the old enqueue message
- Optionally clear `processing_started_at` if your schema has it, so the verifier doesn't treat it as stuck

Example (single record; replace `RECORD_ID` with the actual UUID):

```sql
UPDATE verification_records
SET status = 'queued', error = NULL
WHERE id = 'RECORD_ID'
  AND status = 'failed'
  AND tx_digest IS NULL;
```

To requeue in bulk (use with care; run the `SELECT` above first and limit with an `AND id = ANY(...)` or similar):

```sql
UPDATE verification_records
SET status = 'queued', error = NULL
WHERE status = 'failed'
  AND (error ILIKE '%enqueue%' OR error ILIKE '%redis%' OR error ILIKE '%ResponseError%')
  AND tx_digest IS NULL;
```

### 3. Verify the Oracle verifier consumes them

1. On the Oracle VM: `docker compose -f docker-compose.prod.yml logs -f verifier`
2. Within the next poll cycle (default 15s), you should see the verifier claim the record(s) and log processing.
3. Check the DB: previously `queued` rows should transition to `confirmed` (with `tx_digest` and `object_id`) or to `failed` with a **chain/verifier** error, not an enqueue error.

If records move to `failed` again, inspect the new `error` value; if it's a real SUI/chain failure, they are not enqueue-only and need different handling (e.g. fix chain config or user data).
