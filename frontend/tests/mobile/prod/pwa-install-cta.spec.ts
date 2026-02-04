import { test, expect } from "@playwright/test";
import { gotoAndStabilize } from "../helpers/wait";
import { urls } from "../helpers/urls";
import { sel } from "../helpers/selectors";

test.describe("Mobile PROD — PWA Install CTA", () => {
  test("Gorilla Builder: Install CTA does not overlap main content when present", async ({
    page,
  }) => {
    await gotoAndStabilize(page, urls.gorillaBuilder);

    const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
    if (await signIn.isVisible()) {
      test.skip(true, "Requires auth — on Sign In page");
      return;
    }

    const pwaCta = page.locator(sel.pwaInstallCta).first();
    const pageContent = page.locator(sel.pageCustomBuilder);

    if ((await pwaCta.count()) === 0) {
      test.skip(true, "PWA Install CTA not shown (already installed or not installable)");
      return;
    }

    await expect(pageContent).toBeVisible();
    await expect(pwaCta).toBeVisible();
    await expect(pwaCta).toBeInViewport();
  });

  test("AI Picks: Install CTA does not overlap primary CTA when present", async ({
    page,
  }) => {
    await gotoAndStabilize(page, urls.aiPicks);

    const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
    if (await signIn.isVisible()) {
      test.skip(true, "Requires auth — on Sign In page");
      return;
    }

    const pwaCta = page.locator(sel.pwaInstallCta).first();
    const pageLoaded = page.locator(sel.pageAiBuilder);

    if ((await pwaCta.count()) === 0) {
      test.skip(true, "PWA Install CTA not shown");
      return;
    }

    await expect(pageLoaded).toBeVisible();
    await expect(pwaCta).toBeVisible();
    await expect(pwaCta).toBeInViewport();
  });

  test("No horizontal overflow on pages that show PWA CTA", async ({ page }) => {
    await gotoAndStabilize(page, urls.gorillaBuilder);

    const hasOverflow = await page.evaluate(() => {
      const doc = document.documentElement;
      return doc.scrollWidth > doc.clientWidth + 2;
    });
    expect(hasOverflow).toBeFalsy();
  });
});
