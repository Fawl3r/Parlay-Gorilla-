export class IqSdkEnv {
  public static assertRequired(): void {
    const missing: string[] = [];

    const signerPrivateKey = process.env.SIGNER_PRIVATE_KEY?.trim();
    const rpc = process.env.RPC?.trim();

    if (!signerPrivateKey) {
      missing.push("SIGNER_PRIVATE_KEY");
    }
    if (!rpc) {
      missing.push("RPC");
    }

    if (missing.length) {
      // Keep the message actionable for Render without leaking secrets.
      throw new Error(
        `Missing required env var(s): ${missing.join(", ")}. ` +
          "Set these on the Render service `parlay-gorilla-inscriptions-worker`."
      );
    }

    // Upstream `iq-sdk` decodes SIGNER_PRIVATE_KEY via `bs58.decode()` at import time.
    // Validate the shape early so failures are obvious (and don't require reading SDK internals).
    const looksLikeBase58 = /^[1-9A-HJ-NP-Za-km-z]+$/.test(signerPrivateKey!);
    if (!looksLikeBase58 || signerPrivateKey!.length < 40) {
      throw new Error(
        "Invalid SIGNER_PRIVATE_KEY. Expected a base58-encoded Solana secret key string (commonly ~88 chars). " +
          "If you have a Solana keypair JSON array, you must convert it to base58 before setting SIGNER_PRIVATE_KEY."
      );
    }

    if (!/^https?:\/\//i.test(rpc!)) {
      throw new Error("Invalid RPC. Expected an http(s) URL to a Solana JSON-RPC endpoint.");
    }
  }
}


