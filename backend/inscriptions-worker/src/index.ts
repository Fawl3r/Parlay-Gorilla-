import { createClient } from "redis";

import { loadConfig } from "./config";
import { logger } from "./services/logging/logger";
import { SavedParlaysRepo } from "./services/db/savedParlaysRepo";
import { ensureIqUserInitialized } from "./services/iq/iqClient";
import { inscribeParlayProof } from "./services/iq/inscribe";
import { IqSdkEnv } from "./services/iq/IqSdkEnv";

type JobPayload = {
  job_name?: string;
  job_id?: string;
  savedParlayId?: string;
  attempt?: number;
  enqueued_at?: string;
};

function safeErrorMessage(err: any): string {
  const name = err?.name ? String(err.name) : "Error";
  const msg = err?.message ? String(err.message) : "";
  const combined = msg ? `${name}: ${msg}` : name;
  // Cap to a reasonable size for DB storage.
  return combined.slice(0, 500);
}

function backoffSeconds(base: number, attempt: number): number {
  const a = Math.max(0, Math.min(10, attempt));
  return Math.min(300, base * Math.pow(2, a)); // cap at 5 minutes
}

async function moveDueDelayed(redis: ReturnType<typeof createClient>, delayedKey: string, queueKey: string) {
  const nowMs = Date.now();
  // Pull a small batch each tick to avoid starving BLPOP.
  const due = await redis.zRangeByScore(delayedKey, 0, nowMs, { LIMIT: { offset: 0, count: 25 } });
  if (!due.length) return;

  const multi = redis.multi();
  for (const item of due) {
    multi.zRem(delayedKey, item);
    multi.rPush(queueKey, item);
  }
  await multi.exec();
}

async function processJob(
  repo: SavedParlaysRepo,
  redis: ReturnType<typeof createClient>,
  cfg: ReturnType<typeof loadConfig>,
  job: JobPayload,
  rawJob: string
) {
  const savedParlayId = (job.savedParlayId || "").trim();
  if (!savedParlayId) {
    logger.warn({ job }, "job missing savedParlayId; skipping");
    return;
  }

  const attempt = Number(job.attempt || 0);
  const record = await repo.getById(savedParlayId);
  if (!record) {
    logger.warn({ savedParlayId }, "saved parlay not found; skipping");
    return;
  }

  if (record.parlay_type !== "custom") {
    logger.warn({ savedParlayId, parlayType: record.parlay_type }, "refusing to inscribe non-custom parlay");
    return;
  }

  if (record.inscription_status === "confirmed") {
    return;
  }

  // Keep status queued while we retry; only mark failed on final attempt.
  await repo.markQueued(savedParlayId);

  try {
    const createdAtIso = record.created_at || new Date().toISOString();
    const { txid } = await inscribeParlayProof({
      parlayId: record.id,
      accountNumber: record.account_number,
      hash: record.content_hash,
      createdAtIso,
      iqDatatype: cfg.iqDatatype,
      iqHandle: cfg.iqHandle,
    });

    await repo.markConfirmed(savedParlayId, record.content_hash, txid);
    logger.info({ savedParlayId, txid }, "inscription confirmed");
  } catch (err: any) {
    const nextAttempt = attempt + 1;
    const maxAttempts = cfg.maxAttempts;

    logger.warn({ savedParlayId, attempt: nextAttempt, maxAttempts, err: err?.message }, "inscription attempt failed");

    if (nextAttempt >= maxAttempts) {
      await repo.markFailed(savedParlayId, safeErrorMessage(err));
      logger.error({ savedParlayId }, "inscription failed permanently");
      return;
    }

    // Schedule retry with exponential backoff.
    const delaySec = backoffSeconds(cfg.backoffBaseSeconds, attempt);
    const runAtMs = Date.now() + delaySec * 1000;
    const updatedJob: JobPayload = { ...job, attempt: nextAttempt };
    const updatedRaw = JSON.stringify(updatedJob);
    await redis.zAdd(cfg.delayedKey, [{ score: runAtMs, value: updatedRaw }]);
  }
}

async function main() {
  const cfg = loadConfig();

  // Ensure required IQ env vars exist early (do not log secrets).
  // The upstream IQ SDK decodes SIGNER_PRIVATE_KEY at import time, so we validate
  // aggressively to keep failures actionable (especially on Render).
  IqSdkEnv.assertRequired();

  const redis = createClient({ url: cfg.redisUrl });
  redis.on("error", (err) => logger.error({ err }, "redis error"));
  await redis.connect();

  const repo = new SavedParlaysRepo(cfg.dbUrl);

  await ensureIqUserInitialized();
  logger.info({ queueKey: cfg.queueKey }, "inscriptions worker started");

  while (true) {
    try {
      await moveDueDelayed(redis, cfg.delayedKey, cfg.queueKey);

      const popped = await redis.blPop(cfg.queueKey, cfg.blpopTimeoutSeconds);
      if (!popped) {
        continue;
      }

      const raw = popped.element as any;
      const rawStr = Buffer.isBuffer(raw) ? raw.toString("utf8") : String(raw);

      let job: JobPayload;
      try {
        job = JSON.parse(rawStr);
      } catch {
        logger.warn({ raw: rawStr.slice(0, 200) }, "invalid job payload (not JSON); skipping");
        continue;
      }

      await processJob(repo, redis, cfg, job, rawStr);
    } catch (loopErr: any) {
      logger.error({ err: loopErr?.message }, "worker loop error; continuing");
      await new Promise((r) => setTimeout(r, 1000));
    }
  }
}

main().catch((err) => {
  logger.error({ err: err?.message }, "worker failed to start");
  process.exit(1);
});


