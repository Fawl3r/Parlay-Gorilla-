const test = require("node:test");
const assert = require("node:assert/strict");
const dotenv = require("dotenv");
const path = require("path");

// Load environment variables from backend/.env
const envPath = path.resolve(__dirname, "../../.env");
dotenv.config({ path: envPath });

// Also check parent directory (backend/.env)
const parentEnvPath = path.resolve(__dirname, "../../../.env");
dotenv.config({ path: parentEnvPath });

const { inscribeParlayProof } = require("../dist/services/iq/inscribe.js");
const { ensureIqUserInitialized } = require("../dist/services/iq/iqClient.js");
const { IqSdkEnv } = require("../dist/services/iq/IqSdkEnv.js");

test("live inscription: validates environment variables", async () => {
  const check = IqSdkEnv.checkRequired();
  
  if (!check.valid) {
    console.error("❌ IQ SDK environment variables are not configured:");
    console.error(check.message);
    console.error("\nTo run live tests, set the following in backend/.env:");
    console.error("  SIGNER_PRIVATE_KEY=your_base58_key");
    console.error("  RPC=https://your.solana.rpc.endpoint");
    console.error("  IQ_HANDLE=ParlayGorilla (optional)");
    console.error("  IQ_DATATYPE=parlay_proof (optional)");
    throw new Error("Missing IQ SDK environment variables");
  }
  
  console.log("✅ IQ SDK environment variables are valid");
  assert.equal(check.valid, true);
});

test("live inscription: initializes IQ user account", async () => {
  const check = IqSdkEnv.checkRequired();
  if (!check.valid) {
    throw new Error("Skipping: IQ SDK not configured");
  }

  try {
    await ensureIqUserInitialized();
    console.log("✅ IQ user account initialized");
  } catch (err) {
    // If already initialized, that's fine
    const msg = String(err?.message || "").toLowerCase();
    if (msg.includes("already") || msg.includes("initialized")) {
      console.log("✅ IQ user account already initialized");
      return;
    }
    throw err;
  }
});

test("live inscription: inscribes a test parlay proof", async () => {
  const check = IqSdkEnv.checkRequired();
  if (!check.valid) {
    throw new Error("Skipping: IQ SDK not configured");
  }

  // Ensure user is initialized first
  try {
    await ensureIqUserInitialized();
  } catch (err) {
    // Ignore if already initialized
  }

  // Create a test parlay proof payload (hash-only for privacy)
  const testInput = {
    parlayId: `test-${Date.now()}`,
    accountNumber: "0000000001",
    hash: "a".repeat(64), // Test hash (64 hex chars) - this proves the parlay without exposing picks
    createdAtIso: new Date().toISOString(),
    iqDatatype: process.env.IQ_DATATYPE?.trim() || "parlay_proof",
    iqHandle: process.env.IQ_HANDLE?.trim() || "ParlayGorilla",
  };

  console.log("\n📝 Test inscription payload (PRIVACY-PRESERVING):");
  console.log(`   Parlay ID: ${testInput.parlayId}`);
  console.log(`   Account Number: ${testInput.accountNumber}`);
  console.log(`   Hash: ${testInput.hash.substring(0, 16)}...${testInput.hash.substring(48)}`);
  console.log(`   Created At: ${testInput.createdAtIso}`);
  console.log(`   IQ Handle: ${testInput.iqHandle}`);
  console.log(`   IQ Datatype: ${testInput.iqDatatype}`);
  console.log("\n🔒 Note: Only the hash is inscribed, NOT the actual picks!");
  console.log("   This provides cryptographic proof without exposing private data.");

  try {
    console.log("\n⏳ Inscribing parlay proof on Solana...");
    const startTime = Date.now();
    
    const result = await inscribeParlayProof(testInput);
    
    const duration = Date.now() - startTime;
    
    assert.ok(result.txid, "Result should contain a transaction ID");
    assert.ok(typeof result.txid === "string", "Transaction ID should be a string");
    assert.ok(result.txid.length > 0, "Transaction ID should not be empty");
    
    console.log(`\n✅ Inscription successful! (took ${duration}ms)`);
    console.log(`   Transaction ID: ${result.txid}`);
    
    // Generate Solscan link
    const solscanBase = process.env.SOLSCAN_BASE_URL || "https://solscan.io/tx";
    const solscanUrl = `${solscanBase}/${result.txid}`;
    console.log(`   View on Solscan: ${solscanUrl}`);
    
    // Verify transaction ID format (Solana signatures are base58, typically 88 chars)
    // But they can vary, so we just check it's not empty and looks reasonable
    assert.ok(result.txid.length >= 32, "Transaction ID should be at least 32 characters");
    
    return result;
  } catch (err) {
    console.error("\n❌ Inscription failed:");
    console.error(`   Error: ${err.message}`);
    if (err.stack) {
      console.error(`   Stack: ${err.stack}`);
    }
    throw err;
  }
});

test("live inscription: handles timeout gracefully", async () => {
  const check = IqSdkEnv.checkRequired();
  if (!check.valid) {
    throw new Error("Skipping: IQ SDK not configured");
  }

  // This test verifies that the timeout mechanism works
  // We can't easily test a real timeout without mocking, but we can verify
  // the function completes within a reasonable time
  const testInput = {
    parlayId: `timeout-test-${Date.now()}`,
    accountNumber: "0000000001",
    hash: "b".repeat(64),
    createdAtIso: new Date().toISOString(),
    iqDatatype: process.env.IQ_DATATYPE?.trim() || "parlay_proof",
    iqHandle: process.env.IQ_HANDLE?.trim() || "ParlayGorilla",
  };

  const startTime = Date.now();
  const timeoutMs = 120000; // 2 minutes max (should complete much faster)

  try {
    const result = await Promise.race([
      inscribeParlayProof(testInput),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error("Test timeout exceeded")), timeoutMs)
      )
    ]);

    const duration = Date.now() - startTime;
    console.log(`✅ Inscription completed in ${duration}ms (timeout test passed)`);
    
    assert.ok(result.txid, "Should have transaction ID");
    assert.ok(duration < timeoutMs, "Should complete before timeout");
  } catch (err) {
    if (err.message === "Test timeout exceeded") {
      throw new Error(`Inscription took longer than ${timeoutMs}ms`);
    }
    throw err;
  }
});

test("live inscription: verifies payload structure (hash-only for privacy)", async () => {
  const { buildParlayProofPayload, buildParlayProofDataString } = require("../dist/services/iq/proofPayload.js");

  const testInput = {
    parlayId: "test-payload-verification",
    accountNumber: "0001234567",
    hash: "c".repeat(64),
    createdAtIso: "2025-01-20T12:00:00.000Z",
  };

  const payload = buildParlayProofPayload(testInput);
  const dataString = buildParlayProofDataString(testInput);

  // Verify payload structure
  assert.equal(payload.type, "PARLAY_GORILLA_CUSTOM");
  assert.equal(payload.schema, "pg_parlay_proof_v3");
  assert.equal(payload.account_number, testInput.accountNumber);
  assert.equal(payload.parlay_id, testInput.parlayId);
  assert.equal(payload.hash, testInput.hash);
  assert.equal(payload.website, "Visit ParlayGorilla.com");
  assert.equal(payload.created_at, testInput.createdAtIso);

  // Verify picks are NOT included (privacy-preserving)
  assert.ok(!("legs" in payload), "Legs should NOT be in payload (private)");
  assert.ok(!("title" in payload), "Title should NOT be in payload (private)");
  assert.ok(!("picks" in payload), "Picks should NOT be in payload (private)");

  // Verify JSON serialization
  const parsed = JSON.parse(dataString);
  assert.deepEqual(parsed, payload);

  // Verify no PII
  assert.ok(!("email" in payload));
  assert.ok(!("user_id" in payload));
  assert.ok(!("username" in payload));

  console.log("✅ Payload structure is correct (hash-only for privacy)");
  console.log(`   Data string length: ${dataString.length} bytes`);
  console.log(`   Hash proves parlay exists without exposing picks`);
});

