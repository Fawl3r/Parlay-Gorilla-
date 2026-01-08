import type { Logger } from "../logging/logger";
import type { RedisClient } from "./redisClient";

export type JobProcessResult =
  | { action: "ack" }
  | { action: "drop" }
  | { action: "requeue"; payload: string; delayMs?: number };

export type JobHandler = (rawPayload: string) => Promise<JobProcessResult>;

function sleep(ms: number): Promise<void> {
  const t = Math.max(0, Math.trunc(ms || 0));
  return new Promise((resolve) => setTimeout(resolve, t));
}

export class ReliableQueueConsumer {
  constructor(
    private readonly redis: RedisClient,
    private readonly queueKey: string,
    private readonly processingKey: string,
    private readonly logger: Logger
  ) {}

  async recoverOrphanedJobs(max: number = 5000): Promise<number> {
    let moved = 0;
    for (let i = 0; i < max; i += 1) {
      const raw = await this.redis.lPop(this.processingKey);
      if (!raw) break;
      await this.redis.rPush(this.queueKey, raw);
      moved += 1;
    }
    if (moved) this.logger.warn({ moved }, "recovered orphaned jobs");
    return moved;
  }

  async run(handler: JobHandler): Promise<void> {
    await this.recoverOrphanedJobs();

    for (;;) {
      const raw = await this.redis.brPopLPush(this.queueKey, this.processingKey, 0);
      if (!raw) continue;

      try {
        const result = await handler(raw);
        if (result.action === "requeue") {
          await this.redis.lRem(this.processingKey, 1, raw);
          if (result.delayMs) await sleep(result.delayMs);
          await this.redis.rPush(this.queueKey, result.payload);
          continue;
        }

        await this.redis.lRem(this.processingKey, 1, raw);
      } catch (err: any) {
        // Best-effort: drop the job from processing to avoid an infinite poison-pill loop.
        await this.redis.lRem(this.processingKey, 1, raw);
        this.logger.error({ err: err?.message || String(err) }, "job handler threw; dropped job");
      }
    }
  }
}


