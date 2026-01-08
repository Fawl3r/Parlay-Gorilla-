import { createClient } from "redis";

import type { Logger } from "../logging/logger";

export type RedisClient = ReturnType<typeof createClient>;

export async function createRedisClient(redisUrl: string, logger: Logger): Promise<RedisClient> {
  const client = createClient({ url: redisUrl });

  client.on("error", (err) => {
    logger.error({ err: (err as any)?.message || String(err) }, "redis client error");
  });

  await client.connect();
  return client;
}


