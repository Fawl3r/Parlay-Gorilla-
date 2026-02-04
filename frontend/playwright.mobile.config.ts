import { defineConfig, devices } from "@playwright/test";
import dotenv from "dotenv";
import { existsSync } from "node:fs";
import path from "node:path";

// Load env from frontend dir (config location) so workers get credentials regardless of cwd
const frontendDir = path.resolve(__dirname);
for (const name of [".env.local", ".env"]) {
  const p = path.join(frontendDir, name);
  if (existsSync(p)) {
    dotenv.config({ path: p, quiet: true });
    break;
  }
}

// Env-driven baseURL: production by default, override via PG_E2E_BASE_URL or PG_MOBILE_BACKEND_URL
const PROD_BASE_URL =
  process.env.PG_E2E_BASE_URL ||
  process.env.PROD_BASE_URL ||
  "https://www.parlaygorilla.com";

// When testing prod, frontend uses same-origin for API. Set backend for login so workers use it.
if (PROD_BASE_URL.includes("parlaygorilla.com")) {
  process.env.PG_MOBILE_BACKEND_URL =
    process.env.PG_BACKEND_URL || process.env.PG_MOBILE_BACKEND_URL || PROD_BASE_URL;
}

// Production base URL for mobile regression (no server needed).
const baseURL =
  process.env.PG_MOBILE_BACKEND_URL ||
  process.env.PG_BACKEND_URL ||
  PROD_BASE_URL;

export default defineConfig({
  testDir: "./tests/mobile",
  timeout: 45_000,
  expect: { timeout: 10_000 },

  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  fullyParallel: true,

  reporter: [
    ["html", { open: "never", outputFolder: "playwright-report" }],
    ["list"],
  ],

  use: {
    baseURL,
    actionTimeout: 12_000,
    navigationTimeout: 30_000,

    screenshot: "only-on-failure",
    video: "retain-on-failure",
    trace: "on-first-retry",

    viewport: { width: 390, height: 844 },
    ignoreHTTPSErrors: true,
  },

  projects: [
    {
      name: "mobile-iphone-14",
      use: { ...devices["iPhone 14"], browserName: "chromium" },
    },
    {
      name: "mobile-pixel-7",
      use: { ...devices["Pixel 7"], browserName: "chromium" },
    },
    {
      name: "mobile-iphone-se",
      use: { ...devices["iPhone SE"], browserName: "chromium" },
    },
  ],

  outputDir: "test-results/mobile",
});
