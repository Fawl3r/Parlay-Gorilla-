import { defineConfig } from "@playwright/test";

// Playwright runs outside of Next.js, so it does NOT automatically load `.env.local`.
// Load it here so tunnel URLs work without manual exports.
import dotenv from "dotenv";
import { existsSync } from "node:fs";

for (const candidate of [".env.local", "frontend/.env.local", ".env", "frontend/.env"]) {
  if (existsSync(candidate)) {
    dotenv.config({ path: candidate });
    break;
  }
}

const backendUrl =
  process.env.PG_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.BACKEND_URL ||
  "http://localhost:8000";

const frontendUrlFromEnv = process.env.PG_FRONTEND_URL || process.env.FRONTEND_URL || "";
const defaultPort = Number(process.env.PW_FRONTEND_PORT || 3100);
const baseUrl = frontendUrlFromEnv || `http://127.0.0.1:${defaultPort}`;

function getPortFromUrl(url: string, fallbackPort: number) {
  try {
    const u = new URL(url);
    const p = Number(u.port);
    return Number.isFinite(p) && p > 0 ? p : fallbackPort;
  } catch {
    return fallbackPort;
  }
}

const shouldStartWebServer = !frontendUrlFromEnv;
const webServerPort = getPortFromUrl(baseUrl, defaultPort);

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  // Keep local runs deterministic and avoid hammering the backend/DB.
  workers: 2,
  reporter: [["list"]],
  use: {
    baseURL: baseUrl,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    extraHTTPHeaders: {
      "x-backend-url": backendUrl,
      // Used by the backend to bypass rate limits in non-production environments.
      "x-e2e-test": "true",
    },
  },
  webServer: shouldStartWebServer
    ? {
        // Use a production server to avoid Next.js on-demand compilation flakes (AgeGate "Loading…" + "Compiling…").
        command: `npm run clean:next && npm run build && npm run start -- -p ${webServerPort}`,
        url: baseUrl,
        reuseExistingServer: !process.env.CI,
        timeout: 300_000,
      }
    : undefined,
});


