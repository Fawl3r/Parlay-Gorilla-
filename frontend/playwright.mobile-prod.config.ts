import { defineConfig, devices } from "@playwright/test";

/**
 * Mobile production debugging config.
 * Run against live production to capture screenshots, traces, and console/network
 * for Cursor to reason about and fix mobile-only issues.
 *
 * Usage:
 *   npx playwright test --config=playwright.mobile-prod.config.ts
 *   npx playwright test tests/mobile/prod/gorilla-builder.spec.ts --config=playwright.mobile-prod.config.ts
 */
const PROD_BASE = "https://www.parlaygorilla.com";

export default defineConfig({
  testDir: "./tests/mobile/prod",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  workers: 1,
  reporter: [["list"]],
  outputDir: "artifacts/playwright",
  use: {
    baseURL: PROD_BASE,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "on-first-retry",
    ...devices["iPhone 14"],
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["iPhone 14"],
        browserName: "chromium",
      },
    },
  ],
});
