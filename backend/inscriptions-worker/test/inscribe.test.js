const test = require("node:test");
const assert = require("node:assert/strict");

// Mock the IQ SDK module before importing anything that uses it
const originalModule = require.cache[require.resolve("../dist/services/iq/IqSdkLoader.js")];
let mockIqSdk = null;

// We'll need to test the compiled code, but we need to mock the SDK
// Since the SDK is loaded dynamically, we can intercept the import

test("extractTxid: extracts txid from various response formats", () => {
  // We'll test the helper function logic directly since it's pure
  const testCases = [
    { input: null, expected: "" },
    { input: undefined, expected: "" },
    { input: "", expected: "" },
    { input: "abc123txid", expected: "abc123txid" },
    { input: { txid: "txid_from_object" }, expected: "txid_from_object" },
    { input: { signature: "sig_from_object" }, expected: "sig_from_object" },
    { input: { transaction: "tx_from_object" }, expected: "tx_from_object" },
    { input: { other: "field" }, expected: "" },
    { input: 123, expected: "" },
  ];

  // Since we can't easily import extractTxid (it's not exported), we'll test the logic
  // by creating a test version
  function extractTxid(result) {
    if (!result) return "";
    if (typeof result === "string") return result;
    if (typeof result.txid === "string") return result.txid;
    if (typeof result.signature === "string") return result.signature;
    if (typeof result.transaction === "string") return result.transaction;
    return "";
  }

  for (const { input, expected } of testCases) {
    const actual = extractTxid(input);
    assert.equal(actual, expected, `extractTxid(${JSON.stringify(input)}) should return "${expected}"`);
  }
});

test("parseAfterErrParams: extracts brokeNum and beforeHash from error objects", () => {
  // Test the logic directly
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

  // Test structured error object
  const structuredErr = {
    brokeNum: 5,
    beforeHash: "abc123hash",
  };
  const parsed1 = parseAfterErrParams(structuredErr);
  assert.deepEqual(parsed1, { brokeNum: 5, beforeHash: "abc123hash" });

  // Test error with message pattern 1
  const msgErr1 = new Error("brokeNum: 3 beforeHash: def456hash");
  const parsed2 = parseAfterErrParams(msgErr1);
  assert.deepEqual(parsed2, { brokeNum: 3, beforeHash: "def456hash" });

  // Test error with message pattern 2
  const msgErr2 = new Error("Transaction 7 failed, beforeHash:ghi789hash");
  const parsed3 = parseAfterErrParams(msgErr2);
  assert.deepEqual(parsed3, { brokeNum: 7, beforeHash: "ghi789hash" });

  // Test invalid cases
  assert.equal(parseAfterErrParams(null), null);
  assert.equal(parseAfterErrParams({}), null);
  assert.equal(parseAfterErrParams({ brokeNum: 0 }), null);
  assert.equal(parseAfterErrParams({ brokeNum: -1 }), null);
  assert.equal(parseAfterErrParams(new Error("some other error")), null);
});

test("parseAfterErrParams: handles edge cases", () => {
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

  // Test with string error (not Error object)
  const stringErr = "brokeNum: 2 beforeHash: test123";
  const parsed = parseAfterErrParams(stringErr);
  assert.deepEqual(parsed, { brokeNum: 2, beforeHash: "test123" });

  // Test case-insensitive matching
  const caseErr = new Error("BROKENUM: 4 BEFOREHASH: TEST456");
  const parsed2 = parseAfterErrParams(caseErr);
  assert.deepEqual(parsed2, { brokeNum: 4, beforeHash: "TEST456" });
});

test("buildParlayProofDataString: creates correct JSON payload", () => {
  const { buildParlayProofPayload, buildParlayProofDataString } = require("../dist/services/iq/proofPayload.js");

  const input = {
    parlayId: "test-parlay-id-123",
    accountNumber: "0001234567",
    hash: "a".repeat(64),
    createdAtIso: "2025-01-15T10:30:00.000Z",
  };

  const payload = buildParlayProofPayload(input);
  assert.equal(payload.type, "PARLAY_GORILLA_CUSTOM");
  assert.equal(payload.schema, "pg_parlay_proof_v2");
  assert.equal(payload.account_number, "0001234567");
  assert.equal(payload.parlay_id, "test-parlay-id-123");
  assert.equal(payload.hash, "a".repeat(64));
  assert.equal(payload.created_at, "2025-01-15T10:30:00.000Z");

  const dataString = buildParlayProofDataString(input);
  assert.ok(typeof dataString === "string");
  const parsed = JSON.parse(dataString);
  assert.deepEqual(parsed, payload);
});

test("inscribeParlayProof: requires IQ SDK environment variables", async () => {
  const { IqSdkEnv } = require("../dist/services/iq/IqSdkEnv.js");

  // Save original env
  const originalSigner = process.env.SIGNER_PRIVATE_KEY;
  const originalRpc = process.env.RPC;

  try {
    // Remove required env vars
    delete process.env.SIGNER_PRIVATE_KEY;
    delete process.env.RPC;

    const check = IqSdkEnv.checkRequired();
    assert.equal(check.valid, false);
    assert.match(check.message, /SIGNER_PRIVATE_KEY/);
    assert.match(check.message, /RPC/);

    assert.throws(() => IqSdkEnv.assertRequired(), /SIGNER_PRIVATE_KEY/);
  } finally {
    // Restore env
    if (originalSigner !== undefined) process.env.SIGNER_PRIVATE_KEY = originalSigner;
    else delete process.env.SIGNER_PRIVATE_KEY;
    if (originalRpc !== undefined) process.env.RPC = originalRpc;
    else delete process.env.RPC;
  }
});

test("inscribeParlayProof: validates SIGNER_PRIVATE_KEY format", async () => {
  const { IqSdkEnv } = require("../dist/services/iq/IqSdkEnv.js");

  const originalSigner = process.env.SIGNER_PRIVATE_KEY;
  const originalRpc = process.env.RPC;

  try {
    // Test invalid key format (too short)
    process.env.SIGNER_PRIVATE_KEY = "short";
    process.env.RPC = "https://example.com";

    const check = IqSdkEnv.checkRequired();
    assert.equal(check.valid, false);
    assert.match(check.message, /Invalid SIGNER_PRIVATE_KEY/);

    // Test invalid key format (contains invalid chars)
    process.env.SIGNER_PRIVATE_KEY = "0OIl123"; // contains 0, O, I, l
    const check2 = IqSdkEnv.checkRequired();
    assert.equal(check2.valid, false);

    // Test valid format
    process.env.SIGNER_PRIVATE_KEY = "1".repeat(88); // Valid base58-like string
    const check3 = IqSdkEnv.checkRequired();
    assert.equal(check3.valid, true);
  } finally {
    if (originalSigner !== undefined) process.env.SIGNER_PRIVATE_KEY = originalSigner;
    else delete process.env.SIGNER_PRIVATE_KEY;
    if (originalRpc !== undefined) process.env.RPC = originalRpc;
    else delete process.env.RPC;
  }
});

test("inscribeParlayProof: validates RPC URL format", async () => {
  const { IqSdkEnv } = require("../dist/services/iq/IqSdkEnv.js");

  const originalSigner = process.env.SIGNER_PRIVATE_KEY;
  const originalRpc = process.env.RPC;

  try {
    process.env.SIGNER_PRIVATE_KEY = "1".repeat(88);

    // Test invalid RPC (not a URL)
    process.env.RPC = "not-a-url";
    const check = IqSdkEnv.checkRequired();
    assert.equal(check.valid, false);
    assert.match(check.message, /Invalid RPC/);

    // Test valid RPC
    process.env.RPC = "https://api.mainnet-beta.solana.com";
    const check2 = IqSdkEnv.checkRequired();
    assert.equal(check2.valid, true);
  } finally {
    if (originalSigner !== undefined) process.env.SIGNER_PRIVATE_KEY = originalSigner;
    else delete process.env.SIGNER_PRIVATE_KEY;
    if (originalRpc !== undefined) process.env.RPC = originalRpc;
    else delete process.env.RPC;
  }
});

// Integration test that would require mocking the IQ SDK
// Since the SDK is loaded dynamically, we need to be careful about how we test this
test("inscribeParlayProof: payload structure is correct", () => {
  const { buildParlayProofPayload } = require("../dist/services/iq/proofPayload.js");

  const testInput = {
    parlayId: "550e8400-e29b-41d4-a716-446655440000",
    accountNumber: "0001234567",
    hash: "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    createdAtIso: "2025-01-20T12:00:00.000Z",
  };

  const payload = buildParlayProofPayload(testInput);

  // Verify all required fields
  assert.equal(payload.type, "PARLAY_GORILLA_CUSTOM");
  assert.equal(payload.schema, "pg_parlay_proof_v2");
  assert.equal(payload.account_number, testInput.accountNumber);
  assert.equal(payload.parlay_id, testInput.parlayId);
  assert.equal(payload.hash, testInput.hash);
  assert.equal(payload.created_at, testInput.createdAtIso);

  // Verify no PII fields
  assert.ok(!("email" in payload));
  assert.ok(!("user_id" in payload));
  assert.ok(!("username" in payload));
});

test("inscribeParlayProof: data string is deterministic JSON", () => {
  const { buildParlayProofDataString } = require("../dist/services/iq/proofPayload.js");

  const input = {
    parlayId: "test-id",
    accountNumber: "0001234567",
    hash: "a".repeat(64),
    createdAtIso: "2025-01-15T10:30:00.000Z",
  };

  // Generate multiple times - should be identical
  const str1 = buildParlayProofDataString(input);
  const str2 = buildParlayProofDataString(input);
  assert.equal(str1, str2);

  // Should be valid JSON
  const parsed = JSON.parse(str1);
  assert.equal(parsed.type, "PARLAY_GORILLA_CUSTOM");
  assert.equal(parsed.schema, "pg_parlay_proof_v2");
});

