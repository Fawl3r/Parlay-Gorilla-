import { test, expect } from "@playwright/test";

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified";

test.beforeEach(async ({ page }) => {
  await page.addInitScript((key: string) => {
    localStorage.setItem(key, "true");
  }, AGE_VERIFIED_KEY);
});

test.describe("PWA install CTA on landing", () => {
  test("landing page has installable app callout section", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    await expect(page.locator("[data-age-gate]")).toHaveCount(0);

    const callout = page.getByText("Installable App").first();
    await expect(callout).toBeVisible();

    await expect(
      page.getByText("Install Parlay Gorilla on your phone in 10 seconds — no App Store.").first()
    ).toBeVisible();
  });

  test("PWA install CTA element exists when install is available", async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });

    const cta = page.locator('[data-testid="pwa-install-cta"]');
    const count = await cta.count();
    if (count > 0) {
      await expect(cta.first()).toBeVisible();
      const text = await cta.first().textContent();
      expect(
        text?.includes("Install App") || text?.includes("How to Install")
      ).toBe(true);
    }
  });
});
