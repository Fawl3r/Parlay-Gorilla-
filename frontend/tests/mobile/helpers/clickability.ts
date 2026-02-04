import type { Locator, Page, TestInfo } from "@playwright/test";
import { expect } from "@playwright/test";

/**
 * Asserts the target is visible, enabled, and clickable (not covered by overlay).
 * On trial click failure, attaches JSON with target box + element at click center
 * so you can see exactly what is blocking the tap.
 */
export async function expectClickableNotCovered(
  page: Page,
  target: Locator,
  testInfo: TestInfo,
  name: string,
): Promise<void> {
  await target.scrollIntoViewIfNeeded();
  await expect(target).toBeVisible();
  await expect(target).toBeEnabled();

  try {
    await target.click({ trial: true });
  } catch (err) {
    const box = await target.boundingBox();
    if (box) {
      const cx = box.x + box.width / 2;
      const cy = box.y + box.height / 2;

      const top = await page.evaluate(
        ({ cx, cy }: { cx: number; cy: number }) => {
          const el = document.elementFromPoint(cx, cy) as HTMLElement | null;
          if (!el) return null;
          return {
            tag: el.tagName,
            id: el.id,
            className: el.className,
            ariaLabel: el.getAttribute("aria-label"),
            testid: el.getAttribute("data-testid"),
            text: (el.innerText || "").slice(0, 120),
          };
        },
        { cx, cy },
      );

      await testInfo.attach(`${name}-click-blocker.json`, {
        body: Buffer.from(JSON.stringify({ box, top }, null, 2), "utf-8"),
        contentType: "application/json",
      });
    }

    throw err;
  }
}
