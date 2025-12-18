## Parlay Gorilla × IQ Labs — Technical Implementation & Planned Usage (Non‑Code Overview)

**Audience:** IQ Labs engineering / protocol team  
**Purpose:** Explain how Parlay Gorilla integrates IQ Labs `code_in` (via `code_in_sdk` / `iq-sdk`) to anchor **custom parlay proofs** on Solana, and how we plan to expand usage.  
**Important:** This document intentionally **does not include source code** or proprietary modeling details. It describes system design, interfaces, and operational behavior at a high level.

---

## Product Context (What the system does)

Parlay Gorilla is a web application that helps users build and evaluate sports parlays (1–20 legs). It includes:

- **Odds ingestion** (external odds provider)
- **Probability + confidence scoring** (proprietary engine)
- **Natural‑language explanation** (AI-assisted, optionally enabled)
- **User accounts + analytics** (history, saved tickets, social sharing)
- **On‑chain proof anchoring** (IQ Labs `code_in`) for *user-built* custom parlays

The goal of the IQ Labs integration is to provide a **timestamped, tamper‑evident proof** that a user saved a specific custom parlay at a specific time, **without posting sensitive or proprietary data on-chain**.

---

## High-Level Architecture

Parlay Gorilla is a monorepo with three runtime services plus managed data stores:

- **Web UI (Next.js / TypeScript)**: user experience, auth session handling, dashboard, analytics, saved parlays, and proof verification UX.
- **API (FastAPI / Python)**: authentication, odds/games APIs, parlay analysis/generation, persistence, and job production for inscriptions.
- **Inscriptions Worker (Node.js / TypeScript)**: background consumer that executes `code_in` and records transaction results.
- **PostgreSQL**: durable storage (users, saved parlays, games/markets/odds, analytics).
- **Redis**: distributed cache + background queue (inscriptions jobs; also used to avoid duplicate scheduled work across instances).

### Data flow at a glance

- User builds/parses a ticket in the UI → calls the API to analyze/save
- API stores the full record in Postgres (private) and computes a deterministic hash
- API enqueues a Redis job for the worker (no private keys on the API tier)
- Worker pulls the job, calls IQ Labs `code_in` against Solana RPC, and updates Postgres with tx + status
- UI displays proof status and links to a block explorer (verification UX)

---

## IQ Labs `code_in` Integration (Current Implementation)

### 1) Proof scope and policy

- **Only custom (user-built) saved parlays** are anchored on-chain.
- **AI-generated parlays are never inscribed** (they may be saved in-app, but no on-chain anchoring is triggered).

This prevents anchoring large volumes of automated outputs and keeps on-chain proofs reserved for explicit user actions (“Save Parlay”).

### 2) Privacy & data minimization (No PII on-chain)

We treat on-chain data as public and immutable. The on-chain payload is designed to contain:

- A **non-PII user identifier** (an `account_number` allocated at user creation)
- A **parlay identifier**
- A **deterministic content hash** (SHA‑256) of a canonical representation of the parlay
- A **timestamp** (UTC)
- A small **schema/type marker** for forward compatibility

We do **not** put emails, usernames, display names, or any personal data on-chain.

### 3) Deterministic hashing strategy (tamper-evident proof)

To avoid “hash churn” (e.g., user selects the same legs in a different order), the backend computes a deterministic SHA‑256 hash from a canonical payload:

- Canonical JSON serialization (stable formatting)
- Deterministic ordering of legs (stable sort key)
- Inclusion of a schema version and application version for future-proofing

This hash becomes the **proof anchor** and is the only parlay “content” written on-chain (along with minimal metadata).

### 4) Producer/consumer separation (security boundary)

To reduce blast radius and follow least-privilege:

- **FastAPI backend** acts as the **producer**:
  - Validates authenticated user actions
  - Writes saved parlays to Postgres
  - Computes the deterministic hash
  - Enqueues an inscription job to Redis
  - Tracks lifecycle state (`queued`, `confirmed`, `failed`)

- **Node worker** acts as the **consumer**:
  - Holds the **signer private key** (env-provided; never logged)
  - Connects to Solana RPC
  - Executes `iq-sdk` calls (`userInit()`, `codeIn()`, and `codeInAfterErr()` fallback where applicable)
  - Updates Postgres with confirmed tx signature and timestamps

This design ensures that the main API tier never needs Solana signing credentials.

### 5) Job lifecycle, idempotency, and retries

The system is designed to be resilient under transient failures (RPC instability, rate limits, temporary Redis/network issues):

- **Idempotency**
  - If a saved custom parlay is already confirmed, the worker will not re-inscribe.
  - When a user updates a saved custom parlay, a new inscription is only queued if the deterministic content hash changes.

- **Retries**
  - The worker uses exponential backoff (bounded) and a max-attempt policy.
  - After exceeding max attempts, the record is marked `failed` with a safe, non-sensitive error summary.
  - A user-facing “Retry” action is supported for failed custom inscriptions.

- **SDK fallback path**
  - If `codeIn()` fails in a “partial submission” scenario, the worker attempts `codeInAfterErr()` when enough error context is available, then records the final tx signature.

### 6) Verification UX

Once confirmed, the UI presents:

- Proof status (queued/confirmed/failed)
- A transaction link (e.g., Solscan)
- A short hash display + copy action

This provides end-user verifiability without exposing internal databases or proprietary model inputs.

---

## Operational & Deployment Notes

### Deployment model

Primary deployment is designed for a managed platform (Render) with:

- One backend service (FastAPI)
- One frontend service (Next.js)
- One worker service (Node)
- Managed Postgres + managed Redis

### Observability & safety practices

- **Structured logging** (backend + worker), with intentional avoidance of secrets in logs
- **Health endpoints** on the API tier for uptime and debugging
- **Rate limiting** to protect the API and upstream credits
- Redis is required in production to prevent duplicated scheduled work in multi-instance environments

---

## Planned Usage / Expansion of IQ Labs Integration

The current integration anchors a proof of *saved custom parlay content hash*. Planned expansions (subject to product priorities and protocol constraints):

- **Public verification endpoint/page**
  - A dedicated verification flow that takes a parlay proof hash (or saved parlay token) and verifies chain presence + status.

- **Proof receipts + export**
  - Downloadable “proof receipt” (hash + tx + timestamp + schema) for users who want an audit trail.

- **Event-based anchoring (selective)**
  - Optional proofs for other explicitly user-triggered events (e.g., “Publish to Social”, “Lock Ticket”), still keeping on-chain data minimal and non-PII.

- **Key management hardening**
  - Move signer custody to a managed secrets system / HSM-backed approach where supported.
  - Key rotation procedures and stricter runtime permissions on the worker.

- **Throughput + reliability**
  - Metrics for queue depth / processing latency
  - Dead-letter queue patterns for long-lived failures
  - Optional horizontal scaling of the worker with safe idempotency guarantees

---

## What We Need from IQ Labs (Engineering Alignment)

To ensure the integration stays aligned with protocol expectations and best practices:

- **Recommended payload conventions** for `type/schema` naming and any compatibility expectations across versions
- **Guidance on handling partial submission errors** (best parsing patterns for `codeInAfterErr` inputs)
- **Operational recommendations** for RPC selection, rate limits, and transaction confirmation strategy

---

## Confidentiality Note

This overview omits:

- Proprietary probability/edge modeling implementation
- Prompting strategies and model-tuning details
- Source code and internal business logic beyond interface-level descriptions

If IQ Labs requires deeper review (e.g., payload format validation or audit), we can provide targeted excerpts under NDA or in a private review session.



