const test = require("node:test");
const assert = require("node:assert/strict");
const dotenv = require("dotenv");
const path = require("path");

// Load environment variables
const envPath = path.resolve(__dirname, "../../.env");
dotenv.config({ path: envPath });
const parentEnvPath = path.resolve(__dirname, "../../../.env");
dotenv.config({ path: parentEnvPath });

const { buildParlayProofPayload, buildParlayProofDataString } = require("../dist/services/iq/proofPayload.js");

test("inspect transaction: shows what is currently inscribed", () => {
  const testInput = {
    parlayId: "test-parlay-123",
    accountNumber: "0001234567",
    hash: "a".repeat(64),
    createdAtIso: "2025-01-20T12:00:00.000Z",
  };

  const payload = buildParlayProofPayload(testInput);
  const dataString = buildParlayProofDataString(testInput);

  console.log("\n📋 CURRENT ON-CHAIN DATA (Hash-Only Design):");
  console.log("=" .repeat(60));
  console.log(JSON.stringify(payload, null, 2));
  console.log("=" .repeat(60));
  console.log("\n📏 Data size:", dataString.length, "bytes");
  console.log("\n⚠️  NOTE: Only the HASH is inscribed, not the actual parlay picks/legs!");
  console.log("   The hash is computed from the full parlay data (legs, odds, etc.)");
  console.log("   but the actual picks are stored in the database, not on-chain.");
  console.log("\n💡 To see the actual picks, we would need to modify the payload");
  console.log("   to include the legs array from the database.");

  // Verify what's included
  assert.equal(payload.type, "PARLAY_GORILLA_CUSTOM");
  assert.equal(payload.schema, "pg_parlay_proof_v2");
  assert.ok(payload.account_number);
  assert.ok(payload.parlay_id);
  assert.ok(payload.hash);
  assert.ok(payload.created_at);

  // Verify what's NOT included
  assert.ok(!("legs" in payload), "Legs should NOT be in current payload");
  assert.ok(!("picks" in payload), "Picks should NOT be in current payload");
  assert.ok(!("odds" in payload), "Odds should NOT be in current payload");
  assert.ok(!("title" in payload), "Title should NOT be in current payload");
});

test("inspect transaction: shows what COULD be inscribed (with full data)", () => {
  // Example of what the full payload could look like
  const exampleFullPayload = {
    type: "PARLAY_GORILLA_CUSTOM",
    schema: "pg_parlay_proof_v2",
    account_number: "0001234567",
    parlay_id: "test-parlay-123",
    hash: "a".repeat(64), // Keep hash for verification
    created_at: "2025-01-20T12:00:00.000Z",
    // These would be added:
    legs: [
      {
        game_id: "game-123",
        market_type: "spread",
        pick: "Lakers -5.5",
        odds: -110,
        point: -5.5,
      },
      {
        game_id: "game-456",
        market_type: "total",
        pick: "Over 225.5",
        odds: -105,
        point: 225.5,
      },
    ],
    title: "My Custom Parlay",
  };

  const fullDataString = JSON.stringify(exampleFullPayload);
  
  console.log("\n📋 PROPOSED ON-CHAIN DATA (With Full Parlay Data):");
  console.log("=" .repeat(60));
  console.log(JSON.stringify(exampleFullPayload, null, 2));
  console.log("=" .repeat(60));
  console.log("\n📏 Data size:", fullDataString.length, "bytes");
  console.log("\n✅ This would include:");
  console.log("   - All parlay legs/picks");
  console.log("   - Odds for each leg");
  console.log("   - Game information");
  console.log("   - Title");
  console.log("   - Hash (for verification)");
  console.log("\n⚠️  Trade-offs:");
  console.log("   + Users can see picks directly on-chain");
  console.log("   + No need to query database to verify");
  console.log("   - Larger transaction size (more SOL fees)");
  console.log("   - All data is permanently public on-chain");

  assert.ok(exampleFullPayload.legs, "Full payload would include legs");
  assert.ok(exampleFullPayload.title, "Full payload would include title");
});

