const test = require("node:test");
const assert = require("node:assert/strict");

// These tests import the committed `dist/` output to avoid requiring a TS build step
// during unit tests (`node --test`).
//
// IMPORTANT: Do NOT import `dist/services/iq/inscribe.js` here, because it imports
// the IQ SDK which expects real env vars (SIGNER_PRIVATE_KEY/RPC) at module load.
const { buildParlayProofPayload } = require("../dist/services/iq/proofPayload.js");

test("inscription payload: includes account_number and excludes PII fields", () => {
  const payload = buildParlayProofPayload({
    parlayId: "11111111-1111-1111-1111-111111111111",
    accountNumber: "0001234567",
    hash: "a".repeat(64),
    createdAtIso: "2025-01-01T00:00:00.000Z",
    iqDatatype: "parlay_proof",
    iqHandle: "ParlayGorilla",
  });

  assert.equal(payload.schema, "pg_parlay_proof_v3");
  assert.equal(payload.account_number, "0001234567");
  assert.equal(payload.parlay_id, "11111111-1111-1111-1111-111111111111");
  assert.equal(payload.hash.length, 64);
  assert.equal(payload.website, "Visit ParlayGorilla.com");

  // Never include email or internal user ids in the on-chain payload.
  assert.ok(!("email" in payload));
  assert.ok(!("user_id" in payload));
});


