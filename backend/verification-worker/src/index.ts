import "dotenv/config";

import { ConfigLoader } from "./config";
import { createLogger } from "./logging/logger";
import { createPgPool } from "./db/pgPool";
import { VerificationRecordsRepo } from "./db/verificationRecordsRepo";
import { createRedisClient } from "./redis/redisClient";
import { ReliableQueueConsumer } from "./redis/reliableQueueConsumer";
import { SuiProofClient } from "./sui/suiProofClient";
import { VerificationJobHandler } from "./worker/verificationJobHandler";

async function main() {
  const config = ConfigLoader.load();
  const logger = createLogger("verification-worker");

  logger.info(
    {
      queueKey: config.queueKey,
      processingKey: config.processingKey,
      maxAttempts: config.maxAttempts,
      suiModule: config.suiModule,
      suiFunction: config.suiFunction,
    },
    "worker starting"
  );

  const pool = createPgPool(config.databaseUrl, logger);
  const repo = new VerificationRecordsRepo(pool, logger);

  const redis = await createRedisClient(config.redisUrl, logger);
  const consumer = new ReliableQueueConsumer(redis, config.queueKey, config.processingKey, logger);

  const sui = new SuiProofClient(logger, {
    rpcUrl: config.suiRpcUrl,
    privateKey: config.suiPrivateKey,
    packageId: config.suiPackageId,
    moduleName: config.suiModule,
    functionName: config.suiFunction,
  });

  const handler = new VerificationJobHandler(logger, repo, sui, config.maxAttempts);

  const shutdown = async () => {
    logger.info("shutdown requested");
    try {
      await redis.disconnect();
    } catch {}
    try {
      await pool.end();
    } catch {}
    process.exit(0);
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);

  await consumer.run((raw) => handler.handle(raw));
}

main().catch((err) => {
  // eslint-disable-next-line no-console
  console.error(err);
  process.exit(1);
});


