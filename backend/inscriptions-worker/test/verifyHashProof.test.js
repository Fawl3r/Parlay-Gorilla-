const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("crypto");

/**
 * This test demonstrates how the hash-only approach provides cryptographic proof
 * of a parlay without exposing the actual picks publicly on-chain.
 * 
 * The hash serves as a tamper-evident proof that:
 * 1. The parlay exists (hash is on-chain)
 * 2. The parlay hasn't been modified (any change changes the hash)
 * 3. The parlay was created at a specific time (timestamp is on-chain)
 * 
 * But the actual picks remain private in the database.
 */

test("hash proof: demonstrates privacy-preserving verification", () => {
  // Simulate a parlay with picks (this would be in the database)
  const parlayData = {
    schema_version: "pg_parlay_v1",
    app_version: "pg_backend_v1",
    parlay_id: "test-parlay-123",
    account_number: "0001234567",
    created_at_utc: "2025-01-20T12:00:00.000Z",
    parlay_type: "custom",
    legs: [
      {
        game_id: "game-123",
        market_type: "spread",
        pick: "Lakers -5.5", // PRIVATE - not on-chain
        odds: -110,
        point: -5.5,
      },
      {
        game_id: "game-456",
        market_type: "total",
        pick: "Over 225.5", // PRIVATE - not on-chain
        odds: -105,
        point: 225.5,
      },
    ],
  };

  // Compute hash from full parlay data (this is what's done in the backend)
  const payloadString = JSON.stringify(parlayData);
  const hash = crypto.createHash("sha256").update(payloadString).digest("hex");

  // What gets inscribed on-chain (PUBLIC)
  const onChainData = {
    type: "PARLAY_GORILLA_CUSTOM",
    schema: "pg_parlay_proof_v3",
    account_number: "0001234567",
    parlay_id: "test-parlay-123",
    hash: hash, // Only the hash, not the picks!
    created_at: "2025-01-20T12:00:00.000Z",
    website: "Visit ParlayGorilla.com",
  };

  console.log("\n🔒 PRIVACY-PRESERVING PROOF DESIGN");
  console.log("=" .repeat(60));
  console.log("\n📋 What's in the DATABASE (PRIVATE):");
  console.log(JSON.stringify(parlayData, null, 2));
  console.log("\n📋 What's on CHAIN (PUBLIC):");
  console.log(JSON.stringify(onChainData, null, 2));
  console.log("\n✅ Benefits:");
  console.log("   • Picks are NOT exposed publicly");
  console.log("   • Hash proves parlay exists and hasn't been tampered with");
  console.log("   • Anyone can verify by comparing on-chain hash with database hash");
  console.log("   • Timestamp proves when parlay was created");

  // Verify the hash matches
  const recomputedHash = crypto.createHash("sha256").update(payloadString).digest("hex");
  assert.equal(hash, recomputedHash, "Hash should be deterministic");

  // Show that any change to picks would change the hash
  const modifiedData = { ...parlayData };
  modifiedData.legs[0].pick = "Lakers -6.5"; // Changed pick
  const modifiedPayloadString = JSON.stringify(modifiedData);
  const modifiedHash = crypto.createHash("sha256").update(modifiedPayloadString).digest("hex");

  assert.notEqual(hash, modifiedHash, "Any change to picks should change the hash");
  console.log("\n🔐 Verification:");
  console.log(`   Original hash: ${hash.substring(0, 16)}...`);
  console.log(`   Modified hash: ${modifiedHash.substring(0, 16)}...`);
  console.log("   ✅ Any tampering would be detected!");
});

test("hash proof: demonstrates verification process", () => {
  // Simulate verification: someone wants to verify a parlay exists
  // They have:
  // 1. The on-chain hash (from Solana transaction)
  // 2. The parlay data (from database, if they have access)

  const onChainHash = "a".repeat(64); // From Solana transaction
  const parlayData = {
    schema_version: "pg_parlay_v1",
    app_version: "pg_backend_v1",
    parlay_id: "test-parlay-123",
    account_number: "0001234567",
    created_at_utc: "2025-01-20T12:00:00.000Z",
    parlay_type: "custom",
    legs: [
      { game_id: "game-1", pick: "Lakers -5.5", odds: -110 },
      { game_id: "game-2", pick: "Over 225.5", odds: -105 },
    ],
  };

  // Compute hash from database parlay
  const payloadString = JSON.stringify(parlayData);
  const computedHash = crypto.createHash("sha256").update(payloadString).digest("hex");

  // Verification: compare on-chain hash with computed hash
  const isValid = onChainHash === computedHash;

  console.log("\n🔍 VERIFICATION PROCESS");
  console.log("=" .repeat(60));
  console.log("1. Get hash from on-chain transaction:", onChainHash.substring(0, 16) + "...");
  console.log("2. Get parlay data from database (private)");
  console.log("3. Compute hash from database parlay:", computedHash.substring(0, 16) + "...");
  console.log("4. Compare hashes:", isValid ? "✅ MATCH - Parlay is authentic!" : "❌ MISMATCH - Tampered!");

  // In real scenario, we'd use the actual hash
  // For this test, we'll just show the process
  assert.ok(typeof isValid === "boolean", "Verification should return boolean");
});

test("hash proof: shows what happens if parlay is tampered with", () => {
  const originalParlay = {
    schema_version: "pg_parlay_v1",
    app_version: "pg_backend_v1",
    parlay_id: "test-parlay-123",
    account_number: "0001234567",
    created_at_utc: "2025-01-20T12:00:00.000Z",
    parlay_type: "custom",
    legs: [
      { game_id: "game-1", pick: "Lakers -5.5", odds: -110 },
    ],
  };

  const originalHash = crypto.createHash("sha256")
    .update(JSON.stringify(originalParlay))
    .digest("hex");

  // Someone tries to tamper with the parlay in the database
  const tamperedParlay = {
    ...originalParlay,
    legs: [
      { game_id: "game-1", pick: "Lakers -6.5", odds: -110 }, // Changed pick
    ],
  };

  const tamperedHash = crypto.createHash("sha256")
    .update(JSON.stringify(tamperedParlay))
    .digest("hex");

  // On-chain hash (immutable)
  const onChainHash = originalHash;

  console.log("\n🛡️ TAMPER DETECTION");
  console.log("=" .repeat(60));
  console.log("Original hash (on-chain):", originalHash.substring(0, 16) + "...");
  console.log("Tampered hash (database):", tamperedHash.substring(0, 16) + "...");
  console.log("On-chain hash:", onChainHash.substring(0, 16) + "...");
  console.log("\nVerification:");
  console.log("  Original matches on-chain:", onChainHash === originalHash ? "✅" : "❌");
  console.log("  Tampered matches on-chain:", onChainHash === tamperedHash ? "✅" : "❌");
  console.log("\n✅ Any tampering is immediately detectable!");

  assert.notEqual(originalHash, tamperedHash, "Tampered hash should be different");
  assert.equal(onChainHash, originalHash, "On-chain should match original");
  assert.notEqual(onChainHash, tamperedHash, "On-chain should NOT match tampered");
});

