import { test, expect } from "@playwright/test";

test.describe("SafetyModeBanner", () => {
  test("shows Limited data mode when /ops/safety returns YELLOW", async ({ page }) => {
    await page.route("**/ops/safety", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          state: "YELLOW",
          reasons: ["odds_data_stale"],
          telemetry: {},
          safety_mode_enabled: true,
          events: [],
        }),
      })
    );
    await page.goto("/app");
    await expect(page.getByText("Limited data mode")).toBeVisible();
  });

  test("shows Generation paused when /ops/safety returns RED", async ({ page }) => {
    await page.route("**/ops/safety", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          state: "RED",
          reasons: ["error_count_5m=25 >= 25"],
          telemetry: {},
          safety_mode_enabled: true,
          events: [],
        }),
      })
    );
    await page.goto("/app");
    await expect(page.getByText("Generation paused")).toBeVisible();
  });

  test("does not show banner when /ops/safety returns GREEN", async ({ page }) => {
    await page.route("**/ops/safety", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          state: "GREEN",
          reasons: [],
          telemetry: {},
          safety_mode_enabled: true,
          events: [],
        }),
      })
    );
    await page.goto("/app");
    await expect(page.getByText("Limited data mode")).not.toBeVisible();
    await expect(page.getByText("Generation paused")).not.toBeVisible();
  });
});
