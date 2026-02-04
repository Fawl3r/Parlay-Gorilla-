import { test, expect } from "@playwright/test";
import {
  gotoAndStabilize,
  setupAgeGateBypass,
  pathWithAgeParam,
  dismissAgeGateModalIfPresent,
} from "../helpers/wait";
import { urls } from "../helpers/urls";
import { sel } from "../helpers/selectors";
import { attachMobileDiagnostics } from "../helpers/diagnostics";
import { expectClickableNotCovered } from "../helpers/clickability";
import { expectNoStuckLoader, expectNoFatalUIErrors } from "../helpers/health";
import { measureRoutePerf } from "../helpers/perf";
import { expectStableScreenshot } from "../helpers/visual";
import { expectNoHorizontalOverflow } from "../helpers/layout";

test.describe("Mobile PROD — AI Picks", () => {
  test("Visual snapshot — AI Picks", async ({ page }, testInfo) => {
    attachMobileDiagnostics(page, testInfo);
    await gotoAndStabilize(page, urls.aiPicks);
    await expectStableScreenshot(page, testInfo, "ai-picks", {
      fullPage: true,
      maskSelectors: [
        "[data-testid=\"live-marquee\"]",
        "[data-testid=\"toast-container\"], [data-sonner-toast]",
        "[data-testid=\"rotating-odds\"]",
      ],
    });
  });

  test("Loads AI picks and primary CTA is visible", async ({ page }, testInfo) => {
    attachMobileDiagnostics(page, testInfo);
    setupAgeGateBypass(page);
    await measureRoutePerf(page, testInfo, pathWithAgeParam(urls.aiPicks), {
      routeName: "ai-picks",
      maxDomContentLoadedMs: 7000,
      maxNetworkIdleMs: 9000,
    });
    await dismissAgeGateModalIfPresent(page);
    await page.waitForTimeout(800);

    await expectNoStuckLoader(page);
    await expectNoFatalUIErrors(page);
    await expectNoHorizontalOverflow(page);

    if (process.env.CI) {
      await page.screenshot({
        path: `test-results/mobile/smoke-ai-picks-${Date.now()}.png`,
        fullPage: true,
      });
    }

    const aiRoot = page.locator(sel.aiPicksRoot).or(page.locator(sel.aiPicksRootFallback)).first();
    await expect(aiRoot).toBeVisible().catch(async () => {
      await expect(page.locator("text=/Parlay|Picks|Build/i").first()).toBeVisible();
    });

    const generateBtn = page.locator(sel.generateBtn).first();
    await expect(generateBtn).toBeVisible();
  });

  test("Primary CTA is clickable and not covered", async ({ page }, testInfo) => {
    attachMobileDiagnostics(page, testInfo);
    await gotoAndStabilize(page, urls.aiPicks);

    const generateBtn = page.locator(sel.generateBtn).first();
    await expectClickableNotCovered(page, generateBtn, testInfo, "ai-generate");
  });

  test("Generate flow returns a result OR explains why it cannot", async ({ page }, testInfo) => {
    attachMobileDiagnostics(page, testInfo);
    await gotoAndStabilize(page, urls.aiPicks);

    const legsInput = page.locator(sel.legsInput).first();
    if ((await legsInput.count()) > 0) {
      await legsInput.fill("2");
    }

    await page.locator(sel.generateBtn).first().click();

    const result = page.locator(sel.resultsCard).first();
    const failMessage = page.locator(
      "text=/no games|no odds|out of season|try again|not enough/i",
    ).first();
    await expect(result.or(failMessage)).toBeVisible({ timeout: 20_000 });
  });

  test("No horizontal overflow", async ({ page }, testInfo) => {
    attachMobileDiagnostics(page, testInfo);
    await gotoAndStabilize(page, urls.aiPicks);
    await expectNoHorizontalOverflow(page);
  });

  test("Key mobile controls are not clipped below the fold", async ({ page }, testInfo) => {
    attachMobileDiagnostics(page, testInfo);
    await gotoAndStabilize(page, urls.aiPicks);

    const btn = page.locator(sel.generateBtn).first();
    await btn.scrollIntoViewIfNeeded();
    await expect(btn).toBeVisible();
  });
});
