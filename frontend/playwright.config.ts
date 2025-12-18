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

const baseUrl = process.env.PG_FRONTEND_URL || process.env.FRONTEND_URL || "http://localhost:3000";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  workers: process.env.CI ? 2 : undefined,
  reporter: [["list"]],
  use: {
    baseURL: baseUrl,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    extraHTTPHeaders: {
      "x-backend-url": backendUrl,
    },
  },
});


