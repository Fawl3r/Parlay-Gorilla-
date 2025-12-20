export class IqSdkEnv {
  /**
   * Check if required env vars are present and valid, returning a status object.
   * Use this when you want to handle missing env vars gracefully (e.g., exit cleanly).
   */
  public static checkRequired(): { valid: boolean; message: string } {
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
      return {
        valid: false,
        message: `Missing required env var(s): ${missing.join(", ")}. ` +
          "Set these on the Render service `parlay-gorilla-inscriptions-worker` to enable inscriptions. " +
          "Worker will exit gracefully until configured."
      };
    }

    // Upstream `iq-sdk` decodes SIGNER_PRIVATE_KEY via `bs58.decode()` at import time.
    // Validate the shape early so failures are obvious (and don't require reading SDK internals).
    const looksLikeBase58 = /^[1-9A-HJ-NP-Za-km-z]+$/.test(signerPrivateKey!);
    if (!looksLikeBase58 || signerPrivateKey!.length < 40) {
      return {
        valid: false,
        message: "Invalid SIGNER_PRIVATE_KEY. Expected a base58-encoded Solana secret key string (commonly ~88 chars). " +
          "If you have a Solana keypair JSON array, you must convert it to base58 before setting SIGNER_PRIVATE_KEY."
      };
    }

    if (!/^https?:\/\//i.test(rpc!)) {
      return {
        valid: false,
        message: "Invalid RPC. Expected an http(s) URL to a Solana JSON-RPC endpoint."
      };
    }

    return { valid: true, message: "IQ SDK environment variables are valid." };
  }

  /**
   * Assert that required env vars are present and valid, throwing if not.
   * Use this when the SDK is actually needed (e.g., in IqSdkLoader).
   */
  public static assertRequired(): void {
    const check = IqSdkEnv.checkRequired();
    if (!check.valid) {
      throw new Error(check.message);
    }
  }
}


