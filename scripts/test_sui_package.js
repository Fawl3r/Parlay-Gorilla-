/**
 * Quick test to verify the Sui package ID is correct and can create proofs.
 * 
 * Usage:
 *   cd backend/verification-worker
 *   node ../../scripts/test_sui_package.js
 * 
 * Env:
 *   SUI_RPC_URL=https://fullnode.mainnet.sui.io:443
 *   SUI_PRIVATE_KEY=suiprivkey1qqtp62xx7nw390qtqwp0nx9ecjaju6tq8mwes4yrhe8f35ne6zc8jha6cfd
 *   SUI_PACKAGE_ID=0xa93e3d74da1ecc6ef6fe331237f352946ff42567cbab6080c983fe489ff21574
 */

const { SuiClient } = require("@mysten/sui/client");
const { Transaction } = require("@mysten/sui/transactions");
const { Ed25519Keypair } = require("@mysten/sui/keypairs/ed25519");
const { decodeSuiPrivateKey } = require("@mysten/sui/cryptography");
const crypto = require("crypto");

function parseEd25519Keypair(privateKey) {
  const raw = String(privateKey || "").trim();
  if (!raw) throw new Error("Missing SUI_PRIVATE_KEY");
  
  if (raw.startsWith("suiprivkey")) {
    const decoded = decodeSuiPrivateKey(raw);
    if (decoded.schema !== "ED25519") throw new Error(`Unsupported key scheme: ${decoded.schema}`);
    return Ed25519Keypair.fromSecretKey(decoded.secretKey);
  }
  
  return Ed25519Keypair.fromSecretKey(Uint8Array.from(Buffer.from(raw, "base64")));
}

function hexToBytes32(hex) {
  const h = String(hex || "").trim().toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(h)) throw new Error("Invalid data_hash hex (expected 64 hex chars)");
  return Uint8Array.from(Buffer.from(h, "hex"));
}

async function testCreateProof() {
  const rpcUrl = process.env.SUI_RPC_URL || "https://fullnode.mainnet.sui.io:443";
  const privateKey = process.env.SUI_PRIVATE_KEY || "suiprivkey1qqtp62xx7nw390qtqwp0nx9ecjaju6tq8mwes4yrhe8f35ne6zc8jha6cfd";
  const packageId = process.env.SUI_PACKAGE_ID || "0xa93e3d74da1ecc6ef6fe331237f352946ff42567cbab6080c983fe489ff21574";
  const moduleName = "parlay_proof";
  const functionName = "create_proof";

  console.log("Testing Sui Package...");
  console.log(`RPC URL: ${rpcUrl}`);
  console.log(`Package ID: ${packageId}`);
  console.log(`Module: ${moduleName}`);
  console.log(`Function: ${functionName}`);
  console.log("");

  const client = new SuiClient({ url: rpcUrl });
  const signer = parseEd25519Keypair(privateKey);

  // Create a test hash (32 bytes = 64 hex chars)
  const testData = "test verification record " + Date.now();
  const hash = crypto.createHash("sha256").update(testData).digest("hex");
  const hashBytes = hexToBytes32(hash);
  const createdAt = BigInt(Math.floor(Date.now() / 1000));

  console.log(`Test data: ${testData}`);
  console.log(`Data hash: ${hash}`);
  console.log(`Created at: ${createdAt}`);
  console.log("");

  const tx = new Transaction();
  tx.setGasBudget(BigInt(50_000_000));
  tx.moveCall({
    target: `${packageId}::${moduleName}::${functionName}`,
    arguments: [
      tx.pure.vector("u8", Array.from(hashBytes)),
      tx.pure.u64(createdAt),
    ],
  });

  console.log("Submitting transaction...");
  try {
    const res = await client.signAndExecuteTransaction({
      signer: signer,
      transaction: tx,
      options: {
        showEffects: true,
        showObjectChanges: true,
      },
    });

    const txDigest = String(res?.digest || "").trim();
    if (!txDigest) throw new Error("Missing transaction digest");

    console.log(`✅ SUCCESS!`);
    console.log(`Transaction Digest: ${txDigest}`);
    
    // Extract created Proof object ID
    const objectChanges = res?.objectChanges || [];
    for (const change of objectChanges) {
      if (change.type === "created") {
        const objectType = String(change.objectType || "");
        if (objectType.includes("::parlay_proof::Proof")) {
          console.log(`Proof Object ID: ${change.objectId}`);
          break;
        }
      }
    }

    console.log("");
    console.log("✅ Package ID is correct and proof creation works!");
    return 0;
  } catch (error) {
    console.error("❌ FAILED:", error.message);
    if (error.message.includes("Package")) {
      console.error("   → Check that the package ID is correct");
    }
    if (error.message.includes("gas")) {
      console.error("   → Check that the wallet has sufficient SUI for gas");
    }
    return 1;
  }
}

if (require.main === module) {
  testCreateProof()
    .then((code) => process.exit(code))
    .catch((err) => {
      console.error("Fatal error:", err);
      process.exit(1);
    });
}

module.exports = { testCreateProof };

