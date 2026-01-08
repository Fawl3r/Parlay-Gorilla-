# Verification Records

Parlay Gorilla automatically creates **verification records** for every **Custom AI parlay** generated through the Custom Builder.

These records provide a **permanent, time-stamped confirmation** of *when* a specific parlay analysis existed, without publishing any personal data or proprietary analysis inputs.

## What this is (and isn't)

- **Is**: an automatic, tamper-resistant, time-stamped verification record created server-side for every Custom AI parlay.
- **Is not**: a user-visible "crypto" feature, a per-use purchase, or something users manually trigger.
- **Is not**: related to payments or billing (internal integrity infrastructure only).

## When a verification record is created

- **Automatic** for every Custom AI parlay generated via:
  - `/api/parlay/analyze` (standard analysis)
  - `/api/parlay/counter` (counter/hedge tickets)
  - `/api/parlay/coverage` (coverage pack tickets)
- Created **server-side** immediately after parlay generation.
- **Idempotent**: the same parlay (same fingerprint) will only ever be verified once.
- **No user action required**: verification is a silent integrity layer.

## Data minimization

Verification records store **hashes only**.

- No emails, usernames, display names, or other PII are included in the verification payload.
- The payload is deterministic and hashed (SHA-256) before being recorded.

## Deterministic fingerprinting (anti-abuse)

Every Custom AI parlay generates a **deterministic fingerprint** that serves as the idempotency key for verification.

### Fingerprint Inputs

- `user_id`: The user who generated the parlay
- `sorted(matchup_ids)`: Game/matchup IDs, sorted for stability
- `markets`: Market types (h2h, spreads, totals)
- `odds_snapshot`: Snapshot of odds at generation time
- `model_version`: AI model version used
- `generation_window`: Rounded timestamp bucket (5-10 minute window)

### Properties

- **Same parlay → same fingerprint**: Identical inputs always produce the same fingerprint
- **Regeneration safety**: Re-running analysis with identical data produces the same fingerprint
- **Abuse prevention**: Prevents replay attacks and spam verification attempts
- **Database hard-stop**: Unique constraint on `parlay_fingerprint` ensures a parlay can only be verified once

## Runtime components

- **Backend API (FastAPI)**: validates the request, builds the canonical payload hash, stores metadata, and queues a job.
- **Verification Worker (Node)**: consumes queued jobs, writes an immutable verification record, and persists the resulting record identifiers and timestamps back to the database.
- **Database (Postgres)**: stores saved parlays and verification record metadata for retrieval and internal viewing.

## User experience copy (product-safe)

**UI Language (read-only display):**
- "Verified Analysis"
- "This parlay includes a permanent time-stamped verification record"
- "View verification record" (link to detail page)

**Banned terms (never use):**
- ❌ "inscription"
- ❌ "blockchain"
- ❌ "crypto"
- ❌ "token"
- ❌ "on-chain"
- ❌ "Verify" (as a button/action - verification is automatic)

**UI Behavior:**
- No buttons or user-triggered verification actions
- No "verify again" options
- Read-only status display with optional viewer link


