# Verification Records (Optional)

Parlay Gorilla supports **optional verification records** for **Custom** saved parlays.

These records provide a **permanent, time-stamped confirmation** of *when* a specific parlay hash existed, without publishing any personal data or proprietary analysis inputs.

## What this is (and isn’t)

- **Is**: a tamper-resistant, time-stamped verification record created only when the user opts in.
- **Is not**: a required feature, a user-visible “crypto” feature, or a per-use purchase.

## When a verification record is created

- Only for **Custom** saved parlays.
- Only when the user explicitly selects **Verify (optional)**.
- The request is authenticated and rate-limited.
- Plan policy is enforced server-side:
  - Premium includes a monthly verification cap.
  - After the included cap is exhausted, Premium users may continue by spending credits (per verification).

## Data minimization

Verification records store **hashes only**.

- No emails, usernames, display names, or other PII are included in the verification payload.
- The payload is deterministic and hashed (SHA-256) before being recorded.

## Deterministic hashing

Parlay Gorilla computes a deterministic content hash from a canonical payload:

- Stable schema + app version
- Saved parlay id
- Non-PII account number (stable identifier)
- Created-at timestamp (UTC)
- Deterministically ordered legs snapshot (stable sort key)

This prevents “hash churn” from ordering differences and produces stable verification guarantees.

## Runtime components

- **Backend API (FastAPI)**: validates the request, builds the canonical payload hash, stores metadata, and queues a job.
- **Verification Worker (Node)**: consumes queued jobs, writes an immutable verification record, and persists the resulting record identifiers and timestamps back to the database.
- **Database (Postgres)**: stores saved parlays and verification record metadata for retrieval and internal viewing.

## User experience copy (product-safe)

- “Verification record”
- “Optional time-stamped verification”
- “Tamper-proof confirmation”

Avoid user-facing terminology like wallets, tokens, chains, or crypto.


