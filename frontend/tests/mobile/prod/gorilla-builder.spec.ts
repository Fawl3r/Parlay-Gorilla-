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

test.describe("Mobile PROD — Gorilla Builder", () => {
  test("Visual snapshot — Gorilla Builder", async ({ page }, testInfo) => {
    attachMobileDiagnostics(page, testInfo);
    await gotoAndStabilize(page, urls.gorillaBuilder);
    await expectStableScreenshot(page, testInfo, "gorilla-builder", {
      fullPage: true,
      maskSelectors: [
        "[data-testid=\"live-marquee\"]",
        "[data-testid=\"toast-container\"], [data-sonner-toast]",
        "[data-testid=\"rotating-odds\"]",
      ],
    });
  });

  test("Loads and core UI is visible", async ({ page }, testInfo) => {
    attachMobileDiagnostics(page, testInfo);
    setupAgeGateBypass(page);
    await measureRoutePerf(page, testInfo, pathWithAgeParam(urls.gorillaBuilder), {
      routeName: "gorilla-builder",
      maxDomContentLoadedMs: 6000,
      maxNetworkIdleMs: 8000,
    });
    await dismissAgeGateModalIfPresent(page);
    await page.waitForTimeout(800);

    await expectNoStuckLoader(page);
    await expectNoFatalUIErrors(page);
    await expectNoHorizontalOverflow(page);

    if (process.env.CI) {
      await page.screenshot({
        path: `test-results/mobile/smoke-gorilla-builder-${Date.now()}.png`,
        fullPage: true,
      });
    }

    const builderRoot = page.locator(sel.builderRoot).or(page.locator(sel.builderRootFallback)).first();
    await expect(builderRoot).toBeVisible();
    const analyzeBtn = page.locator(sel.analyzeBtn).or(page.locator(sel.analyzeBtnFallback));
    await expect(analyzeBtn.first()).toBeVisible();
  });

  test("Primary CTA is clickable and not covered", async ({ page }, testInfo) => {
    attachMobileDiagnostics(page, testInfo);
    await gotoAndStabilize(page, urls.gorillaBuilder);

    const analyzeBtn = page.locator(sel.analyzeBtn).or(page.locator(sel.analyzeBtnFallback)).first();
    await expectClickableNotCovered(page, analyzeBtn, testInfo, "builder-analyze");
  });

  test("Template click populates slip OR shows a meaningful empty-state", async ({ page }, testInfo) => {
    attachMobileDiagnostics(page, testInfo);
    await gotoAndStabilize(page, urls.gorillaBuilder);

    const template = page.locator(sel.safe2PickTemplate).first();
    await template.click({ force: true }).catch(async () => {
      await page.locator(sel.balancedTemplate).first().click({ force: true });
    });

    const picksHeader = page.locator(sel.picksHeader).first();
    const noGamesCopy = page.locator("text=/no games|no odds|out of season|no markets/i");
    await expect(picksHeader.or(noGamesCopy)).toBeVisible();
  });

  test("Analyze button is tappable and does not get stuck behind overlays", async ({ page }, testInfo) => {
    attachMobileDiagnostics(page, testInfo);
    await gotoAndStabilize(page, urls.gorillaBuilder);

    const analyze = page.locator(sel.analyzeBtn).or(page.locator(sel.analyzeBtnFallback)).first();
    await analyze.scrollIntoViewIfNeeded();
    await expect(analyze).toBeVisible();
    await analyze.click();

    const analysisVisible = page.locator("text=/Analysis|Breakdown|Matchup/i");
    const toastOrMessage = page
      .locator(sel.toast)
      .or(page.locator("text=/add at least|no picks|not enough/i"));
    await expect(analysisVisible.or(toastOrMessage)).toBeVisible();
  });

  test("No horizontal overflow (common mobile break)", async ({ page }, testInfo) => {
    attachMobileDiagnostics(page, testInfo);
    await gotoAndStabilize(page, urls.gorillaBuilder);
    await expectNoHorizontalOverflow(page);
  });

  test("Modal or sheet is scrollable on mobile (if present)", async ({ page }, testInfo) => {
    attachMobileDiagnostics(page, testInfo);
    await gotoAndStabilize(page, urls.gorillaBuilder);

    const addPick = page.locator(sel.addPickBtn).first();
    if ((await addPick.count()) === 0) {
      test.skip(true, "No Add Pick button found — skipping modal scroll check.");
      return;
    }
    await addPick.click();

    const modal = page
      .locator(
        '[role="dialog"], [data-state="open"][data-radix-dialog-content], [data-testid="sheet-content"]',
      )
      .first();
    await expect(modal).toBeVisible({ timeout: 8000 });
    await expectNoHorizontalOverflow(page);

    const scrolled = await page.evaluate(() => {
      const el =
        document.querySelector('[role="dialog"]') ||
        document.querySelector("[data-state=\"open\"][data-radix-dialog-content]") ||
        document.querySelector("[data-testid=\"sheet-content\"]");
      if (!el) return false;
      const before = (el as HTMLElement).scrollTop;
      (el as HTMLElement).scrollTop = before + 200;
      const after = (el as HTMLElement).scrollTop;
      return after > before;
    });
    expect(scrolled).toBeTruthy();
  });
});
