import { Pool } from "pg";

import type { Logger } from "../logging/logger";

export function createPgPool(databaseUrl: string, logger: Logger): Pool {
  const pool = new Pool({
    connectionString: databaseUrl,
    max: Number(process.env.PG_POOL_MAX || 5),
  });

  pool.on("error", (err) => {
    logger.error({ err: err?.message }, "pg pool error");
  });

  return pool;
}


