import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";

/**
 * Assert no horizontal overflow (zero sideways scroll). Call after load and after opening modals/sheets.
 */
export async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  const overflow = await page.evaluate(() => {
    const doc = document.documentElement;
    return doc.scrollWidth > doc.clientWidth + 2;
  });
  expect(overflow, "Detected horizontal overflow on mobile").toBeFalsy();
}
