import pino from "pino";

export type Logger = pino.Logger;

export function createLogger(serviceName: string): Logger {
  return pino({
    name: serviceName,
    level: process.env.LOG_LEVEL || "info",
    redact: {
      paths: [
        "SUI_PRIVATE_KEY",
        "SUI_RPC_URL",
        "DATABASE_URL",
        "REDIS_URL",
        "*.SUI_PRIVATE_KEY",
        "*.DATABASE_URL",
        "*.REDIS_URL",
      ],
      remove: true,
    },
  });
}


