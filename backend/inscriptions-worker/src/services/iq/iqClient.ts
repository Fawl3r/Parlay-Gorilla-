import { logger } from "../logging/logger";
import { IqSdkLoader } from "./IqSdkLoader";

let initialized = false;

export async function ensureIqUserInitialized(): Promise<void> {
  if (initialized) return;
  try {
    const iqsdk = await IqSdkLoader.load();
    await iqsdk.userInit();
    initialized = true;
    logger.info("IQ user account initialized");
  } catch (err: any) {
    // If the user is already initialized, the SDK may throw. Treat as success.
    const msg = String(err?.message || "");
    if (msg.toLowerCase().includes("already") || msg.toLowerCase().includes("initialized")) {
      initialized = true;
      logger.info("IQ user already initialized");
      return;
    }
    throw err;
  }
}



