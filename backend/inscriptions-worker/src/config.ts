import dotenv from "dotenv";

export type SolanaCluster = "mainnet" | "devnet";

export interface WorkerConfig {
  redisUrl: string;
  queueKey: string;
  delayedKey: string;
  blpopTimeoutSeconds: number;
  dbUrl: string;
  maxAttempts: number;
  backoffBaseSeconds: number;
  iqHandle: string;
  iqDatatype: string;
}

function requireEnv(key: string): string {
  const value = process.env[key];
  if (!value || !value.trim()) {
    throw new Error(`Missing required env var: ${key}`);
  }
  return value.trim();
}

function normalizePostgresUrl(url: string): string {
  // Backend prefers asyncpg URLs; Node/pg does not.
  if (url.startsWith("postgresql+asyncpg://")) {
    return url.replace("postgresql+asyncpg://", "postgresql://");
  }
  if (url.startsWith("postgres+asyncpg://")) {
    return url.replace("postgres+asyncpg://", "postgresql://");
  }
  return url;
}

export function loadConfig(): WorkerConfig {
  // Best-effort local env support.
  dotenv.config();

  const redisUrl = requireEnv("REDIS_URL");
  const dbUrl = normalizePostgresUrl(process.env.PG_DATABASE_URL?.trim() || requireEnv("DATABASE_URL"));

  return {
    redisUrl,
    queueKey: process.env.INSCRIPTION_QUEUE_KEY?.trim() || "parlay_gorilla:queue:inscribe_custom_parlay",
    delayedKey: process.env.INSCRIPTION_DELAYED_KEY?.trim() || "parlay_gorilla:queue:inscribe_custom_parlay:delayed",
    blpopTimeoutSeconds: Number(process.env.INSCRIPTION_BLPOP_TIMEOUT_SECONDS || 5),
    dbUrl,
    maxAttempts: Number(process.env.INSCRIPTION_MAX_ATTEMPTS || 5),
    backoffBaseSeconds: Number(process.env.INSCRIPTION_BACKOFF_BASE_SECONDS || 5),
    iqHandle: process.env.IQ_HANDLE?.trim() || "ParlayGorilla",
    iqDatatype: process.env.IQ_DATATYPE?.trim() || "parlay_proof",
  };
}



