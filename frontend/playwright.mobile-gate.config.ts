import { defineConfig, devices } from "@playwright/test";
import dotenv from "dotenv";
import { existsSync } from "node:fs";
import path from "node:path";

const frontendDir = path.resolve(__dirname);
for (const name of [".env.local", ".env"]) {
  const p = path.join(frontendDir, name);
  if (existsSync(p)) {
    dotenv.config({ path: p, quiet: true });
    break;
  }
}

const PROD_BASE_URL =
  process.env.PG_E2E_BASE_URL ||
  process.env.PROD_BASE_URL ||
  "https://www.parlaygorilla.com";

if (PROD_BASE_URL.includes("parlaygorilla.com")) {
  process.env.PG_MOBILE_BACKEND_URL =
    process.env.PG_BACKEND_URL || process.env.PG_MOBILE_BACKEND_URL || PROD_BASE_URL;
}

const baseURL =
  process.env.PG_MOBILE_BACKEND_URL ||
  process.env.PG_BACKEND_URL ||
  PROD_BASE_URL;

/**
 * Mobile UX + Performance gate. Runs against production (or PG_E2E_BASE_URL).
 * Use: npm run test:mobile:gate
 */
export default defineConfig({
  testDir: "./tests/e2e/mobile-gate",
  timeout: 60_000,
  expect: { timeout: 10_000 },

  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  fullyParallel: true,

  reporter: [
    ["html", { open: "never", outputFolder: "playwright-report-gate" }],
    ["list"],
  ],

  use: {
    baseURL,
    actionTimeout: 12_000,
    navigationTimeout: 45_000,

    screenshot: "only-on-failure",
    video: "retain-on-failure",
    trace: "retain-on-failure",

    viewport: { width: 390, height: 844 },
    ignoreHTTPSErrors: true,
  },

  projects: [
    { name: "mobile-iphone-14", use: { ...devices["iPhone 14"], browserName: "chromium" } },
    { name: "mobile-pixel-7", use: { ...devices["Pixel 7"], browserName: "chromium" } },
  ],

  outputDir: "test-results/mobile-gate",
});
