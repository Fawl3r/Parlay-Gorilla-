export type WorkerConfig = {
  databaseUrl: string;
  redisUrl: string;
  queueKey: string;
  processingKey: string;
  maxAttempts: number;

  suiRpcUrl: string;
  suiPrivateKey: string;
  suiPackageId: string;
  suiModule: string;
  suiFunction: string;
};

function required(name: string): string {
  const v = String(process.env[name] || "").trim();
  if (!v) throw new Error(`Missing required env var: ${name}`);
  return v;
}

function optional(name: string, fallback: string): string {
  const v = String(process.env[name] || "").trim();
  return v || fallback;
}

function intEnv(name: string, fallback: number, min: number, max: number): number {
  const raw = String(process.env[name] || "").trim();
  if (!raw) return fallback;
  const n = Math.trunc(Number(raw));
  if (!Number.isFinite(n)) return fallback;
  return Math.max(min, Math.min(max, n));
}

export class ConfigLoader {
  static load(): WorkerConfig {
    const queueKey = optional("VERIFICATION_QUEUE_KEY", "parlay_gorilla:queue:verify_saved_parlay");
    return {
      databaseUrl: optional("PG_DATABASE_URL", "") || required("DATABASE_URL"),
      redisUrl: required("REDIS_URL"),
      queueKey,
      processingKey: `${queueKey}:processing`,
      maxAttempts: intEnv("VERIFICATION_MAX_ATTEMPTS", 5, 1, 10),

      suiRpcUrl: required("SUI_RPC_URL"),
      suiPrivateKey: required("SUI_PRIVATE_KEY"),
      suiPackageId: required("SUI_PACKAGE_ID"),
      suiModule: optional("SUI_MODULE", "parlay_proof"),
      suiFunction: optional("SUI_FUNCTION", "create_proof"),
    };
  }
}


