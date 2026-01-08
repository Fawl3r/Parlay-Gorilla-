import type { Logger } from "../logging/logger";
import type { JobProcessResult } from "../redis/reliableQueueConsumer";
import type { VerificationRecordsRepo } from "../db/verificationRecordsRepo";
import type { SuiProofClient } from "../sui/suiProofClient";

type JobPayload = {
  job_name: string;
  job_id: string;
  verificationRecordId: string;
  savedParlayId: string;
  attempt?: number;
  enqueued_at?: string;
};

function safeParseJob(raw: string): JobPayload | null {
  try {
    const obj = JSON.parse(raw);
    if (!obj || typeof obj !== "object") return null;
    return obj as JobPayload;
  } catch {
    return null;
  }
}

function backoffMs(attempt: number): number {
  const a = Math.max(0, Math.min(10, Math.trunc(attempt || 0)));
  return Math.min(60_000, 1000 * Math.pow(2, a));
}

export class VerificationJobHandler {
  constructor(
    private readonly logger: Logger,
    private readonly repo: VerificationRecordsRepo,
    private readonly sui: SuiProofClient,
    private readonly maxAttempts: number
  ) {}

  async handle(raw: string): Promise<JobProcessResult> {
    const job = safeParseJob(raw);
    if (!job) {
      this.logger.warn("invalid job payload (not json)");
      return { action: "drop" };
    }

    if (job.job_name !== "verify_saved_parlay") {
      this.logger.warn({ job_name: job.job_name }, "unexpected job_name");
      return { action: "drop" };
    }

    const recordId = String(job.verificationRecordId || "").trim();
    if (!recordId) return { action: "drop" };

    const record = await this.repo.getById(recordId);
    if (!record) {
      this.logger.warn({ recordId }, "verification record not found; dropping job");
      return { action: "drop" };
    }

    if (record.status === "confirmed") {
      return { action: "ack" };
    }

    const attempt = Math.max(0, Math.trunc(Number(job.attempt || 0)));
    const nextAttempt = attempt + 1;

    try {
      const createdAtSeconds = Math.floor(new Date(record.created_at).getTime() / 1000);
      const result = await this.sui.createProof(record.data_hash, createdAtSeconds);
      await this.repo.markConfirmed(record.id, result.txDigest, result.objectId);
      return { action: "ack" };
    } catch (err: any) {
      const msg = err?.message || String(err);
      await this.repo.setLastError(record.id, msg);

      if (nextAttempt >= Math.max(1, this.maxAttempts)) {
        await this.repo.markFailed(record.id, msg);
        return { action: "drop" };
      }

      const updated: JobPayload = { ...job, attempt: nextAttempt };
      return { action: "requeue", payload: JSON.stringify(updated), delayMs: backoffMs(attempt) };
    }
  }
}


