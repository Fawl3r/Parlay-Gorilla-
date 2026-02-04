import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";

const DEFAULT_BAD_TEXT = [
  "Something went wrong",
  "Unexpected error",
  "Failed to fetch",
  "Network Error",
  "Server error",
];

/**
 * If a loader/spinner is visible, it must disappear within the timeout.
 * Call after gotoAndStabilize to fail fast on stuck loaders.
 */
export async function expectNoStuckLoader(page: Page): Promise<void> {
  const spinners = page.locator(
    '[data-testid="loading"], [aria-busy="true"], .spinner, .animate-spin',
  );
  await page.waitForTimeout(800);

  if (await spinners.first().isVisible().catch(() => false)) {
    await expect(spinners.first()).toBeHidden({ timeout: 15_000 });
  }
}

/**
 * Fail if fatal error copy is visible (e.g. "Something went wrong", "Network Error").
 */
export async function expectNoFatalUIErrors(page: Page): Promise<void> {
  for (const t of DEFAULT_BAD_TEXT) {
    const hit = page.getByText(t, { exact: false });
    if (await hit.first().isVisible().catch(() => false)) {
      throw new Error(`Fatal UI error text detected: "${t}"`);
    }
  }
}
