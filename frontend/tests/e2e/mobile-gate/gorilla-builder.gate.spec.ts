/**
 * @gate Mobile UX + Performance gate — Gorilla Builder
 * Runs against production (or PG_E2E_BASE_URL). Requires E2E account; fails (never skips) if auth missing or builder unreachable.
 * Cold load: each test runs in a new context (default). Budgets apply to this cold path.
 */
import { test, expect } from "@playwright/test";
import { gotoWithRequiredAuth } from "../../mobile/helpers/wait";
import { hasMobileTestCredentials } from "../../mobile/helpers/auth";
import { urls } from "../../mobile/helpers/urls";
import { sel } from "../../mobile/helpers/selectors";
import { startUXProbe, getUXProbeResults, installNetworkTimingListeners, clearNetworkTimings } from "../helpers/perf";
import { perfBudgets, coldBudgets } from "../helpers/perf_budgets";

test.describe("Mobile UX + Perf Gate — Gorilla Builder @gate", () => {
  test.beforeEach(async ({ page }) => {
    page.on("console", (msg) => {
      const text = msg.text();
      if (text.includes("error") || text.includes("Error")) console.log("[page]", text);
    });
    page.on("pageerror", (err) => console.log("[pageerror]", err.message));
  });

  test("Gorilla Builder: feedback, API, long-task and LCP-ish budgets (cold load)", async ({ page, request }) => {
    // Non-skippable: fail if E2E creds missing (gate must require auth when app does).
    expect(
      hasMobileTestCredentials(),
      "Gate requires PG_MOBILE_TEST_EMAIL and PG_MOBILE_TEST_PASSWORD. Set in CI secrets and frontend/.env.local.",
    ).toBe(true);

    clearNetworkTimings();
    const urlPatterns = ["/api/parlay", "/api/custom-parlay", "/parlay/hedges"];
    installNetworkTimingListeners(page, urlPatterns);

    await test.step("Install UX probe before load", async () => {
      await startUXProbe(page);
    });

    await test.step("Navigate to builder (required auth)", async () => {
      await gotoWithRequiredAuth(page, request, urls.gorillaBuilder);
    });

    await test.step("Builder root visible", async () => {
      const root = page.locator(sel.builderRoot).or(page.locator(sel.builderRootFallback));
      await expect(root.first()).toBeVisible({ timeout: 25_000 });
    });

    const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
    const stillOnSignIn = await signIn.isVisible().catch(() => false);
    if (stillOnSignIn) {
      await expect(signIn).toBeHidden({ timeout: 0 }).catch(() => {});
      expect(stillOnSignIn, "Gate must reach builder; Sign In page still visible — auth or redirect failed.").toBe(false);
    }

    await test.step("Add picks via template", async () => {
      const template = page.locator(sel.safe2PickTemplate).or(page.locator('[data-testid="pg-add-pick"]')).first();
      const visible = await template.isVisible().catch(() => false);
      if (!visible) {
        const balanced = page.locator(sel.balancedTemplate).first();
        if (await balanced.isVisible().catch(() => false)) await balanced.click({ force: true });
      } else {
        await template.click({ force: true });
      }
      await page.waitForTimeout(1500);
    });

    const analyzeBtn = page.locator(sel.analyzeBtn).or(page.locator(sel.analyzeBtnFallback)).first();
    const analyzeVisible = await analyzeBtn.isVisible().catch(() => false);
    expect(analyzeVisible, "Gate requires Analyze button visible; builder UI may be broken or picks not added.").toBe(true);

    const tapTime = Date.now();
    const feedbackLoc = page.locator("text=/Analyzing|Get AI Analysis/i").or(page.locator(sel.breakdownModal)).or(page.locator(sel.toast));

    await test.step("Tap Analyze and check tap-to-feedback (LCP-ish: time to first skeleton/feedback)", async () => {
      await analyzeBtn.scrollIntoViewIfNeeded();
      await analyzeBtn.click();

      const feedbackVisible = await feedbackLoc.first().waitFor({ state: "visible", timeout: perfBudgets.timeToFirstSkeletonMs + 500 }).catch(() => false);
      const timeToFirstSkeletonMs = feedbackVisible ? Date.now() - tapTime : 9999;

      expect(timeToFirstSkeletonMs, `Time to first skeleton/feedback should be <= ${perfBudgets.timeToFirstSkeletonMs}ms`).toBeLessThanOrEqual(perfBudgets.timeToFirstSkeletonMs);
      expect(timeToFirstSkeletonMs, `Tap-to-feedback (cold) should be <= ${coldBudgets.tapToFeedbackMs}ms`).toBeLessThanOrEqual(coldBudgets.tapToFeedbackMs);
    });

    const feedbackVisibleAt = Date.now();

    await test.step("Wait for results and measure spinner duration + results visible", async () => {
      const breakdown = page.locator(sel.breakdownModal);
      const toast = page.locator(sel.toast).first();
      const message = page.locator("text=/add at least|no picks|not enough/i");
      await expect(breakdown.or(toast).or(message)).toBeVisible({ timeout: coldBudgets.timeToResultsMs + 2000 });
    });

    const resultsVisibleAt = Date.now();
    const resultsVisibleMs = resultsVisibleAt - tapTime;
    const spinnerVisibleDurationMs = resultsVisibleAt - feedbackVisibleAt;

    await test.step("Enforce LCP-ish: spinner duration and results visible within budget", async () => {
      expect(resultsVisibleMs, `Results visible (tap to results) should be <= ${perfBudgets.resultsVisibleMs}ms`).toBeLessThanOrEqual(perfBudgets.resultsVisibleMs);
      expect(resultsVisibleMs, `Cold load results should be <= ${coldBudgets.timeToResultsMs}ms`).toBeLessThanOrEqual(coldBudgets.timeToResultsMs);
      expect(spinnerVisibleDurationMs, `Spinner visible duration should be <= ${perfBudgets.spinnerVisibleDurationMs}ms`).toBeLessThanOrEqual(perfBudgets.spinnerVisibleDurationMs);
    });

    await test.step("Enforce API and long-task budgets", async () => {
      const results = await getUXProbeResults(page);

      const relevantApi = results.apiTimings.filter(
        (t) => t.name.includes("/parlay") || t.name.includes("hedges"),
      );
      for (const t of relevantApi) {
        expect(t.ms, `API ${t.name} should be <= ${perfBudgets.apiResponseMs}ms`).toBeLessThanOrEqual(perfBudgets.apiResponseMs);
      }

      expect(results.longTasksCount, "Long tasks count").toBeLessThanOrEqual(perfBudgets.longTasksCount);
      expect(results.worstLongTaskMs, "Worst long task ms").toBeLessThanOrEqual(perfBudgets.worstLongTaskMs);

      console.log(
        "[perf]",
        JSON.stringify({
          longTasksCount: results.longTasksCount,
          worstLongTaskMs: results.worstLongTaskMs,
          resultsVisibleMs,
          apiTimings: results.apiTimings.slice(-5),
        }),
      );
    });
  });
});
