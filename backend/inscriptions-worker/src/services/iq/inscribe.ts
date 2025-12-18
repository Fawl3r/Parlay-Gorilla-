import iqsdk from "iq-sdk";
import { logger } from "../logging/logger";
import { buildParlayProofDataString, type ParlayProofPayloadInput } from "./proofPayload";

export type InscribeParlayProofInput = ParlayProofPayloadInput & {
  iqDatatype: string;
  iqHandle: string;
};

function extractTxid(result: any): string {
  if (!result) return "";
  if (typeof result === "string") return result;
  if (typeof result.txid === "string") return result.txid;
  if (typeof result.signature === "string") return result.signature;
  if (typeof result.transaction === "string") return result.transaction;
  return "";
}

function withTimeout<T>(promise: Promise<T>, ms: number, label: string): Promise<T> {
  let timeout: NodeJS.Timeout | undefined;
  const guard = new Promise<T>((_, reject) => {
    timeout = setTimeout(() => reject(new Error(`${label} timed out after ${ms}ms`)), ms);
  });
  return Promise.race([promise, guard]).finally(() => {
    if (timeout) clearTimeout(timeout);
  }) as Promise<T>;
}

function parseAfterErrParams(err: any): { brokeNum: number; beforeHash: string } | null {
  // Prefer structured fields if the SDK ever throws them.
  const brokeNum = Number((err as any)?.brokeNum);
  const beforeHash = (err as any)?.beforeHash ? String((err as any).beforeHash) : "";
  if (Number.isFinite(brokeNum) && brokeNum > 0 && beforeHash) {
    return { brokeNum, beforeHash };
  }

  // Best-effort parse common patterns from an error message.
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

export async function inscribeParlayProof(input: InscribeParlayProofInput): Promise<{ txid: string }> {
  const dataString = buildParlayProofDataString(input);

  try {
    const res = await withTimeout(
      iqsdk.codeIn(dataString, input.iqDatatype, input.iqHandle),
      60_000,
      "iqsdk.codeIn"
    );
    const txid = extractTxid(res);
    if (!txid) {
      throw new Error("IQ SDK returned empty tx signature");
    }
    return { txid };
  } catch (err: any) {
    // Fallback path per SDK docs (`codeInAfterErr`) for partial submission edge cases.
    // Only attempt when we can extract the required (brokeNum, beforeHash) from the error.
    const parsed = parseAfterErrParams(err);
    if (!parsed) {
      throw err;
    }

    logger.warn({ err: err?.message, ...parsed }, "codeIn failed; attempting codeInAfterErr");
    const res2 = await withTimeout(
      iqsdk.codeInAfterErr(parsed.brokeNum, parsed.beforeHash, dataString, input.iqDatatype, input.iqHandle),
      60_000,
      "iqsdk.codeInAfterErr"
    );
    const txid2 = extractTxid(res2);
    if (!txid2) {
      throw new Error("IQ SDK returned empty tx signature after codeInAfterErr");
    }
    return { txid: txid2 };
  }
}


