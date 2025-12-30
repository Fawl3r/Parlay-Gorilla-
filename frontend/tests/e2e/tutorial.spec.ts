import { test, expect } from "@playwright/test";

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified";

test.beforeEach(async ({ page }) => {
  await page.addInitScript((key: string) => {
    localStorage.setItem(key, "true");
  }, AGE_VERIFIED_KEY);
});

test.describe("Tutorial page", () => {
  test("loads and renders core sections", async ({ page }) => {
    await page.goto("/tutorial", { waitUntil: "domcontentloaded" });

    // AgeGate should not block tests (we seed localStorage).
    await expect(page.locator("[data-age-gate]")).toHaveCount(0);

    // Must not redirect to login or elsewhere - this is the key test
    await expect(page).toHaveURL(/\/tutorial\/?(\?.*)?$/);

    // Wait for page to load
    await page.waitForLoadState("domcontentloaded");

    // Quick Start block should be present (mobile-first confidence builder)
    await expect(page.locator('[data-testid="tutorial-quick-start"]')).toBeVisible();

    // Basic check: page should have some content (body should not be empty)
    const bodyText = await page.locator("body").textContent();
    expect(bodyText).toBeTruthy();
    expect(bodyText!.length).toBeGreaterThan(0);
  });

  test("renders tutorial screenshots when present", async ({ page }) => {
    await page.goto("/tutorial", { waitUntil: "domcontentloaded" });

    await expect(page.locator("[data-age-gate]")).toHaveCount(0);

    // Wait for page to fully load
    await page.waitForLoadState("networkidle");

    // Check that screenshot components are rendered (if any)
    const screenshots = page.locator('[data-testid="tutorial-screenshot"]');
    const count = await screenshots.count();
    
    // If screenshots exist, check their attributes
    if (count > 0) {
      const firstScreenshot = screenshots.first();
      await expect(firstScreenshot).toHaveAttribute("data-screenshot-id");
      await expect(firstScreenshot).toHaveAttribute("data-variant");
    }
  });

  test("table of contents links navigate to sections", async ({ page }) => {
    await page.goto("/tutorial", { waitUntil: "domcontentloaded" });

    await expect(page.locator("[data-age-gate]")).toHaveCount(0);

    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Find a TOC link and click it
    const tocLink = page.getByRole("link", { name: /Start here/i }).first();
    if (await tocLink.isVisible()) {
      await tocLink.click();
      // Should scroll to the section (hash navigation)
      await page.waitForTimeout(500); // Allow scroll to complete
      const url = page.url();
      expect(url).toMatch(/\/tutorial/);
    }
  });
});

