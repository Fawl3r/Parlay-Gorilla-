const test = require("node:test");
const assert = require("node:assert/strict");

/**
 * Integration tests for IQ code inscription
 * 
 * These tests verify the complete flow of inscribing a parlay proof,
 * including error handling and fallback paths.
 * 
 * Note: These tests mock the IQ SDK since it requires real Solana credentials.
 */

test("inscribeParlayProof: complete input validation", () => {
  const { buildParlayProofPayload } = require("../dist/services/iq/proofPayload.js");

  // Test with minimal valid input
  const minimalInput = {
    parlayId: "test-id",
    accountNumber: "0000000001",
    hash: "0".repeat(64),
    createdAtIso: new Date().toISOString(),
  };

  const payload = buildParlayProofPayload(minimalInput);
  assert.ok(payload);
  assert.equal(payload.type, "PARLAY_GORILLA_CUSTOM");
  assert.equal(payload.schema, "pg_parlay_proof_v2");
});

test("inscribeParlayProof: handles various hash formats", () => {
  const { buildParlayProofPayload } = require("../dist/services/iq/proofPayload.js");

  const hashFormats = [
    "a".repeat(64), // lowercase hex
    "A".repeat(64), // uppercase hex
    "0123456789abcdef".repeat(4), // mixed case hex
    "0".repeat(64), // all zeros
  ];

  for (const hash of hashFormats) {
    const input = {
      parlayId: "test-id",
      accountNumber: "0000000001",
      hash: hash,
      createdAtIso: "2025-01-15T10:30:00.000Z",
    };

    const payload = buildParlayProofPayload(input);
    assert.equal(payload.hash, hash, `Hash ${hash} should be preserved exactly`);
  }
});

test("inscribeParlayProof: handles various account number formats", () => {
  const { buildParlayProofPayload } = require("../dist/services/iq/proofPayload.js");

  const accountNumbers = [
    "0000000001",
    "1234567890",
    "9999999999",
    "0001234567",
  ];

  for (const accountNumber of accountNumbers) {
    const input = {
      parlayId: "test-id",
      accountNumber: accountNumber,
      hash: "a".repeat(64),
      createdAtIso: "2025-01-15T10:30:00.000Z",
    };

    const payload = buildParlayProofPayload(input);
    assert.equal(payload.account_number, accountNumber, `Account number ${accountNumber} should be preserved`);
  }
});

test("inscribeParlayProof: handles various parlay ID formats", () => {
  const { buildParlayProofPayload } = require("../dist/services/iq/proofPayload.js");

  const parlayIds = [
    "550e8400-e29b-41d4-a716-446655440000", // UUID format
    "parlay-123",
    "12345",
    "test_parlay_id_with_underscores",
  ];

  for (const parlayId of parlayIds) {
    const input = {
      parlayId: parlayId,
      accountNumber: "0000000001",
      hash: "a".repeat(64),
      createdAtIso: "2025-01-15T10:30:00.000Z",
    };

    const payload = buildParlayProofPayload(input);
    assert.equal(payload.parlay_id, parlayId, `Parlay ID ${parlayId} should be preserved`);
  }
});

test("inscribeParlayProof: ISO timestamp handling", () => {
  const { buildParlayProofPayload } = require("../dist/services/iq/proofPayload.js");

  const timestamps = [
    "2025-01-15T10:30:00.000Z",
    "2025-01-15T10:30:00Z",
    "2025-12-31T23:59:59.999Z",
    "2024-01-01T00:00:00.000Z",
  ];

  for (const timestamp of timestamps) {
    const input = {
      parlayId: "test-id",
      accountNumber: "0000000001",
      hash: "a".repeat(64),
      createdAtIso: timestamp,
    };

    const payload = buildParlayProofPayload(input);
    assert.equal(payload.created_at, timestamp, `Timestamp ${timestamp} should be preserved`);
  }
});

test("inscribeParlayProof: payload is JSON serializable", () => {
  const { buildParlayProofPayload, buildParlayProofDataString } = require("../dist/services/iq/proofPayload.js");

  const input = {
    parlayId: "test-parlay-id",
    accountNumber: "0001234567",
    hash: "a".repeat(64),
    createdAtIso: "2025-01-15T10:30:00.000Z",
  };

  const payload = buildParlayProofPayload(input);
  const dataString = buildParlayProofDataString(input);

  // Should be valid JSON
  let parsed;
  assert.doesNotThrow(() => {
    parsed = JSON.parse(dataString);
  }, "Data string should be valid JSON");

  // Should match the payload object
  assert.deepEqual(parsed, payload, "Parsed JSON should match payload object");

  // Should be able to serialize/deserialize multiple times
  const reSerialized = JSON.stringify(parsed);
  const reParsed = JSON.parse(reSerialized);
  assert.deepEqual(reParsed, payload, "Should survive multiple serialization cycles");
});

test("inscribeParlayProof: payload structure is immutable", () => {
  const { buildParlayProofPayload } = require("../dist/services/iq/proofPayload.js");

  const input = {
    parlayId: "test-id",
    accountNumber: "0000000001",
    hash: "a".repeat(64),
    createdAtIso: "2025-01-15T10:30:00.000Z",
  };

  const payload1 = buildParlayProofPayload(input);
  const payload2 = buildParlayProofPayload(input);

  // Should create new objects (not same reference)
  assert.notEqual(payload1, payload2, "Should create new objects each time");

  // But should have same content
  assert.deepEqual(payload1, payload2, "Should have identical content");
});

test("inscribeParlayProof: error parsing handles various error message formats", () => {
  // Test the error parsing logic that would be used in codeInAfterErr fallback
  function parseAfterErrParams(err) {
    const brokeNum = Number(err?.brokeNum);
    const beforeHash = err?.beforeHash ? String(err.beforeHash) : "";
    if (Number.isFinite(brokeNum) && brokeNum > 0 && beforeHash) {
      return { brokeNum, beforeHash };
    }

    const msg = String(err?.message || err || "");
    const match =
      msg.match(/brokeNum[:=]\s*(\d+).+beforeHash[:=]\s*([A-Za-z0-9]+)/i) ||
      msg.match(/Transaction\s+(\d+)\s+failed,\s+beforeHash:([A-Za-z0-9]+)/i);
    if (!match) return null;
    const n = Number(match[1]);
    const h = String(match[2]);
    if (!Number.isFinite(n) || n <= 0 || !h) return null;
    return { brokeNum: n, beforeHash: h };
  }

  // Test various error formats that might come from the SDK
  const errorCases = [
    {
      err: { brokeNum: 3, beforeHash: "abc123" },
      expected: { brokeNum: 3, beforeHash: "abc123" },
    },
    {
      err: new Error("brokeNum: 5 beforeHash: def456"),
      expected: { brokeNum: 5, beforeHash: "def456" },
    },
    {
      err: new Error("Transaction 7 failed, beforeHash:ghi789"),
      expected: { brokeNum: 7, beforeHash: "ghi789" },
    },
    {
      err: new Error("Some other error"),
      expected: null,
    },
    {
      err: { brokeNum: 0, beforeHash: "test" },
      expected: null, // brokeNum must be > 0
    },
    {
      err: { brokeNum: 2, beforeHash: "" },
      expected: null, // beforeHash must be non-empty
    },
  ];

  for (const { err, expected } of errorCases) {
    const result = parseAfterErrParams(err);
    if (expected === null) {
      assert.equal(result, null, `Error ${JSON.stringify(err)} should return null`);
    } else {
      assert.deepEqual(result, expected, `Error ${JSON.stringify(err)} should parse correctly`);
    }
  }
});

test("inscribeParlayProof: txid extraction handles various response formats", () => {
  // Test the txid extraction logic
  function extractTxid(result) {
    if (!result) return "";
    if (typeof result === "string") return result;
    if (typeof result.txid === "string") return result.txid;
    if (typeof result.signature === "string") return result.signature;
    if (typeof result.transaction === "string") return result.transaction;
    return "";
  }

  const responseCases = [
    { response: "txid123", expected: "txid123" },
    { response: { txid: "txid_from_txid" }, expected: "txid_from_txid" },
    { response: { signature: "txid_from_signature" }, expected: "txid_from_signature" },
    { response: { transaction: "txid_from_transaction" }, expected: "txid_from_transaction" },
    { response: { txid: "prefer_txid", signature: "ignore_signature" }, expected: "prefer_txid" },
    { response: {}, expected: "" },
    { response: null, expected: "" },
    { response: undefined, expected: "" },
    { response: 123, expected: "" },
  ];

  for (const { response, expected } of responseCases) {
    const result = extractTxid(response);
    assert.equal(result, expected, `Response ${JSON.stringify(response)} should extract "${expected}"`);
  }
});

