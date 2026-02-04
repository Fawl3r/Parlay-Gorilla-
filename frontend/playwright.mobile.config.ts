import { defineConfig, devices } from "@playwright/test";

const PROD_BASE_URL =
  process.env.PROD_BASE_URL || "https://www.parlaygorilla.com";

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
