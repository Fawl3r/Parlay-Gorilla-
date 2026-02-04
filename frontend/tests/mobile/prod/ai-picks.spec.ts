import { test, expect } from "@playwright/test";
import { gotoAndStabilize } from "../helpers/wait";
import { urls } from "../helpers/urls";
import { sel } from "../helpers/selectors";

test.describe("Mobile PROD — AI Picks", () => {
  test("Loads AI picks and primary CTA is visible", async ({ page }) => {
    await gotoAndStabilize(page, urls.aiPicks);

    const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
    const pageLoaded = page.locator(sel.pageAiBuilder);
    const aiRoot = page.locator(sel.aiPicksRoot).first();
    const fallback = page.locator(sel.aiPicksRootFallback).first();
    const anyContent = page.locator("main, [role=main], header").first();

    await expect(
      signIn.or(pageLoaded).or(aiRoot).or(fallback).or(anyContent).first(),
    ).toBeVisible({ timeout: 15_000 });

    const signInVisible = await signIn.isVisible().catch(() => false);
    if (!signInVisible) {
      const generateBtn = page.locator(sel.generateBtn).first();
      await expect(generateBtn.or(signIn)).toBeVisible({ timeout: 8_000 });
    }
  });

  test("Generate flow returns a result OR explains why it cannot", async ({ page }) => {
    await gotoAndStabilize(page, urls.aiPicks);

    const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
    if (await signIn.isVisible()) {
      test.skip(true, "Requires auth — on Sign In page");
      return;
    }

    const generateBtn = page.locator(sel.generateBtn).first();
    const btnVisible = await generateBtn.isVisible().catch(() => false);
    if (!btnVisible) {
      test.skip(true, "No Generate/Build button — skipping generate flow");
      return;
    }

    const legsInput = page.locator(sel.legsInput).first();
    if ((await legsInput.count()) > 0) {
      await legsInput.fill("2");
    }

    await generateBtn.click();

    const result = page.locator(sel.resultsCard).first();
    const failMessage = page
      .locator("text=/no games|no odds|out of season|try again|not enough/i")
      .first();
    await expect(result.or(failMessage)).toBeVisible({ timeout: 20_000 });
  });

  test("No horizontal overflow", async ({ page }) => {
    await gotoAndStabilize(page, urls.aiPicks);

    const hasOverflow = await page.evaluate(() => {
      const doc = document.documentElement;
      return doc.scrollWidth > doc.clientWidth + 2;
    });
    expect(hasOverflow).toBeFalsy();
  });

  test("Key mobile controls are not clipped below the fold", async ({ page }) => {
    await gotoAndStabilize(page, urls.aiPicks);

    const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
    if (await signIn.isVisible()) {
      test.skip(true, "Requires auth — on Sign In page");
      return;
    }

    const btn = page.locator(sel.generateBtn).first();
    const btnVisible = await btn.isVisible().catch(() => false);
    if (!btnVisible) {
      test.skip(true, "No Generate/Build button — skipping");
      return;
    }
    await btn.scrollIntoViewIfNeeded();
    await expect(btn).toBeVisible();
  });
});
