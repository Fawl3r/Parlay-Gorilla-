import { SuiClient } from "@mysten/sui/client";
import { Transaction } from "@mysten/sui/transactions";
import { Ed25519Keypair } from "@mysten/sui/keypairs/ed25519";
import { decodeSuiPrivateKey } from "@mysten/sui/cryptography";

import type { Logger } from "../logging/logger";

export type ProofCreationResult = {
  txDigest: string;
  objectId: string;
};

function hexToBytes32(hex: string): Uint8Array {
  const h = String(hex || "").trim().toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(h)) throw new Error("Invalid data_hash hex (expected 64 hex chars)");
  return Uint8Array.from(Buffer.from(h, "hex"));
}

function parseEd25519Keypair(privateKey: string): Ed25519Keypair {
  const raw = String(privateKey || "").trim();
  if (!raw) throw new Error("Missing SUI_PRIVATE_KEY");

  // Prefer Sui CLI exported format: "suiprivkey..."
  if (raw.startsWith("suiprivkey")) {
    const decoded = decodeSuiPrivateKey(raw);
    if (decoded.schema !== "ED25519") throw new Error(`Unsupported key scheme: ${decoded.schema}`);
    return Ed25519Keypair.fromSecretKey(decoded.secretKey);
  }

  // Fallback: base64-encoded raw secret key bytes.
  return Ed25519Keypair.fromSecretKey(Uint8Array.from(Buffer.from(raw, "base64")));
}

function extractCreatedObjectId(objectChanges: any[] | undefined, expectedSuffix: string): string {
  const changes = Array.isArray(objectChanges) ? objectChanges : [];
  for (const c of changes) {
    if (!c || c.type !== "created") continue;
    const objectType = String(c.objectType || "");
    if (!objectType) continue;
    if (!objectType.endsWith(expectedSuffix)) continue;
    const objectId = String(c.objectId || "");
    if (objectId) return objectId;
  }
  throw new Error("Created proof object id not found in transaction object changes");
}

export class SuiProofClient {
  private readonly client: SuiClient;
  private readonly signer: Ed25519Keypair;

  constructor(
    private readonly logger: Logger,
    opts: {
      rpcUrl: string;
      privateKey: string;
      packageId: string;
      moduleName: string;
      functionName: string;
    }
  ) {
    this.client = new SuiClient({ url: opts.rpcUrl });
    this.signer = parseEd25519Keypair(opts.privateKey);
    this._packageId = opts.packageId;
    this._moduleName = opts.moduleName;
    this._functionName = opts.functionName;
  }

  private readonly _packageId: string;
  private readonly _moduleName: string;
  private readonly _functionName: string;

  async createProof(dataHashHex: string, createdAtSeconds: number): Promise<ProofCreationResult> {
    const hashBytes = hexToBytes32(dataHashHex);
    const createdAt = BigInt(Math.max(0, Math.trunc(createdAtSeconds || 0)));

    const tx = new Transaction();
    // Keep gas usage predictable; override via env if needed.
    tx.setGasBudget(BigInt(Math.max(1, Math.trunc(Number(process.env.SUI_GAS_BUDGET || 50_000_000)))));
    tx.moveCall({
      target: `${this._packageId}::${this._moduleName}::${this._functionName}`,
      arguments: [tx.pure.vector("u8", Array.from(hashBytes)), tx.pure.u64(createdAt)],
    });

    const res: any = await this.client.signAndExecuteTransaction({
      signer: this.signer,
      transaction: tx,
      options: {
        showEffects: true,
        showObjectChanges: true,
      },
    });

    const txDigest = String(res?.digest || "").trim();
    if (!txDigest) throw new Error("Missing transaction digest");

    // Proof type suffix: ::parlay_proof::Proof (package address varies)
    const objectId = extractCreatedObjectId(res?.objectChanges, `::${this._moduleName}::Proof`);

    this.logger.info({ txDigest, objectId }, "verification proof created");
    return { txDigest, objectId };
  }
}


