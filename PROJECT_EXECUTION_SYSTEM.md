# Project Execution System

## Operating mode (default)
Build → Finish → Ship → Fix

## Scope discipline
- Prefer minimal diffs that directly unblock shipping.
- Fix bugs at the **source of truth** (backend/data layer) when possible; keep client-side safeguards small.
- Every non-trivial change must have a regression test or a deterministic verification harness.

## “Done” definition for a change
- User-visible behavior is correct
- Errors handled
- Tests updated/added and passing
- Verification steps documented
