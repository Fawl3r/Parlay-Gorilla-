import type { Page, TestInfo } from "@playwright/test";
import { expect } from "@playwright/test";

type VisualOpts = {
  fullPage?: boolean;
  maskSelectors?: string[];
};

/**
 * Stable screenshot: optional masks for dynamic content, animations disabled.
 * Baseline stored when run with --update-snapshots; also attaches runtime screenshot for CI.
 */
export async function expectStableScreenshot(
  page: Page,
  testInfo: TestInfo,
  name: string,
  opts?: VisualOpts,
): Promise<void> {
  const fullPage = opts?.fullPage ?? true;
  const maskSelectors = opts?.maskSelectors ?? [];

  await page.waitForTimeout(500);

  const masks = maskSelectors.length
    ? maskSelectors.map((sel) => page.locator(sel))
    : undefined;

  await expect(page).toHaveScreenshot(`${name}.png`, {
    fullPage,
    mask: masks,
    animations: "disabled",
  });

  const buf = await page.screenshot({ fullPage });
  await testInfo.attach(`${name}-runtime.png`, {
    body: buf,
    contentType: "image/png",
  });
}
