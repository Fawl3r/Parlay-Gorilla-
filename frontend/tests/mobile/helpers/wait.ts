import type { Page } from "@playwright/test";

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified";

/**
 * Bypass age gate and navigate to path; wait for layout to settle.
 * Use for all prod mobile tests so /app routes load.
 */
export async function gotoAndStabilize(page: Page, path: string): Promise<void> {
  await page.addInitScript((key: string) => {
    localStorage.setItem(key, "true");
  }, AGE_VERIFIED_KEY);

  await page.goto(path, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
}
