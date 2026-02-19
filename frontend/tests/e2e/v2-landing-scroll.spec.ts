import { test, expect } from "@playwright/test";

/**
 * V2 landing scroll behavior.
 * Verifies vertical and horizontal scrolling work without errors or layout thrash.
 */
test.describe("V2 landing scroll", () => {
  test("vertical and horizontal scroll work and content stays visible", async ({ page }) => {
    await page.goto("/v2", { waitUntil: "domcontentloaded" });
    await expect(page).toHaveURL(/\/v2\/?/);

    // Hero should be in view initially
    await expect(page.getByRole("heading", { name: /stop guessing/i })).toBeVisible();

    // Scroll page down (native scroll)
    await page.evaluate(() => window.scrollBy(0, 400));
    await page.waitForTimeout(100);

    await expect(page.getByRole("heading", { name: /today'?s top picks/i })).toBeVisible();

    // Scroll further
    await page.evaluate(() => window.scrollBy(0, 600));
    await page.waitForTimeout(100);

    await expect(page.getByRole("heading", { name: /how it works/i })).toBeVisible();

    // Horizontal strip: find overflow container and scroll it
    const horizontalStrip = page.locator(".v2-scroll-x").first();
    await expect(horizontalStrip).toBeVisible();

    const scrolled = await horizontalStrip.evaluate((el: Element) => {
      const div = el as HTMLDivElement;
      const start = div.scrollLeft;
      div.scrollLeft += 200;
      return div.scrollLeft !== start;
    });
    expect(scrolled).toBe(true);

    // CTA section reachable by scrolling to bottom
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(100);
    await expect(page.getByRole("heading", { name: /ready to build/i })).toBeVisible();
  });
});
