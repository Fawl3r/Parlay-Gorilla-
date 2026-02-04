import type { Page } from "@playwright/test";

const LOADING_SELECTOR = '[data-testid="pg-loading"]';
const SKELETON_SELECTOR = '[data-testid="pg-skeleton"]';
const RESULTS_SELECTOR = '[data-testid="pg-ai-results"]';
const BUILDER_RESULTS_INDICATOR = '[data-testid="parlay-breakdown-modal"], [data-testid="pg-ai-results"]';

/**
 * Waits for a loading indicator (pg-loading or pg-skeleton) to become visible
 * within 300ms–800ms (typical tap-to-feedback window).
 */
export async function waitForLoadingToStart(
  page: Page,
  options: { timeoutMs?: number; minDelayMs?: number } = {},
): Promise<boolean> {
  const timeoutMs = options.timeoutMs ?? 800;
  const minDelayMs = options.minDelayMs ?? 300;
  const loading = page.locator(`${LOADING_SELECTOR}, ${SKELETON_SELECTOR}`).first();
  try {
    await loading.waitFor({ state: "visible", timeout: timeoutMs });
  } catch {
    return false;
  }
  await page.waitForTimeout(minDelayMs);
  return true;
}

/**
 * Waits for loading to finish (loader disappears) and results container to appear.
 */
export async function waitForLoadingToFinish(
  page: Page,
  options: { resultsSelector?: string; timeoutMs?: number } = {},
): Promise<void> {
  const timeoutMs = options.timeoutMs ?? 30_000;
  const resultsSelector = options.resultsSelector ?? `${RESULTS_SELECTOR}, ${BUILDER_RESULTS_INDICATOR}`;
  const loader = page.locator(`${LOADING_SELECTOR}, ${SKELETON_SELECTOR}`).first();
  const results = page.locator(resultsSelector).first();
  await loader.waitFor({ state: "hidden", timeout: timeoutMs }).catch(() => {});
  await results.waitFor({ state: "visible", timeout: timeoutMs });
}
