import { defineConfig, devices } from "@playwright/test";
import dotenv from "dotenv";
import { existsSync } from "node:fs";

// Load env so PG_MOBILE_TEST_* and PG_BACKEND_URL are available in main and workers
for (const candidate of [".env.local", ".env"]) {
  if (existsSync(candidate)) {
    dotenv.config({ path: candidate, quiet: true });
    break;
  }
}

const PROD_BASE_URL =
  process.env.PROD_BASE_URL || "https://www.parlaygorilla.com";

// When testing prod, frontend uses same-origin for API. Set backend for login so workers use it.
if (PROD_BASE_URL.includes("parlaygorilla.com")) {
  process.env.PG_MOBILE_BACKEND_URL =
    process.env.PG_BACKEND_URL || process.env.PG_MOBILE_BACKEND_URL || PROD_BASE_URL;
}

export default defineConfig({
  testDir: "./tests/mobile",
  timeout: 45_000,
  expect: { timeout: 10_000 },

  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,

  reporter: [
    ["html", { open: "never" }],
    ["list"],
  ],

  use: {
    baseURL: PROD_BASE_URL,
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
