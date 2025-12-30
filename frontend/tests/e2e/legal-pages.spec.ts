import { test, expect } from "@playwright/test";

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified";

test.beforeEach(async ({ page }) => {
  await page.addInitScript((key: string) => {
    localStorage.setItem(key, "true");
  }, AGE_VERIFIED_KEY);
});

test.describe("Public legal pages (Stripe/LemonSqueezy checks)", () => {
  test("Footer includes required legal links", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    // AgeGate should not block tests (we seed localStorage).
    await expect(page.locator("[data-age-gate]")).toHaveCount(0);

    const footer = page.locator("footer");
    await expect(footer).toBeVisible();

    await expect(footer.getByRole("link", { name: "Terms" })).toHaveAttribute("href", "/terms");
    await expect(footer.getByRole("link", { name: "Privacy" })).toHaveAttribute("href", "/privacy");
    await expect(footer.getByRole("link", { name: "Refunds" })).toHaveAttribute("href", "/refunds");
    await expect(footer.getByRole("link", { name: "Disclaimer", exact: true })).toHaveAttribute("href", "/disclaimer");

    // Contact email visible as a trust signal
    await expect(footer.getByRole("link", { name: "contact@f3ai.dev", exact: true })).toHaveAttribute(
      "href",
      "mailto:contact@f3ai.dev"
    );
  });

  test("Required pages are public and render content", async ({ page }) => {
    const targets: Array<{ path: string; heading: RegExp }> = [
      { path: "/terms", heading: /Terms of Service/i },
      { path: "/privacy", heading: /Privacy Policy/i },
      { path: "/refunds", heading: /Refund.*Cancellation Policy/i },
      { path: "/disclaimer", heading: /Sports.*Disclaimer/i },
    ];

    for (const t of targets) {
      await page.goto(t.path, { waitUntil: "domcontentloaded" });
      await expect(page.locator("[data-age-gate]")).toHaveCount(0);

      // Must not redirect to login or elsewhere.
      const escapedPath = t.path.replace(/\//g, "\\/");
      await expect(page).toHaveURL(new RegExp(`${escapedPath}\\/?(\\?.*)?$`));

      await expect(page.getByRole("heading", { name: t.heading })).toBeVisible();
      await expect(page.locator('a[href="mailto:contact@f3ai.dev"]').first()).toBeVisible();

      // Footer should always be present (required links are checked separately).
      await expect(page.locator("footer")).toBeVisible();
    }
  });
});


