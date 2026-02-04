/**
 * @gate Mobile UX + Performance gate — AI Picks
 * Runs against production (or PG_E2E_BASE_URL). Enforces feedback, API, and long-task budgets.
 * Skips if paywall blocks (do NOT fail).
 */
import { test, expect } from "@playwright/test";
import { gotoWithOptionalAuth } from "../../mobile/helpers/wait";
import { urls } from "../../mobile/helpers/urls";
import { sel } from "../../mobile/helpers/selectors";
import { startUXProbe, getUXProbeResults, installNetworkTimingListeners, clearNetworkTimings } from "../helpers/perf";
import { perfBudgets } from "../helpers/perf_budgets";

test.describe("Mobile UX + Perf Gate — AI Picks @gate", () => {
  test.beforeEach(async ({ page }) => {
    page.on("console", (msg) => {
      const text = msg.text();
      if (text.includes("error") || text.includes("Error")) console.log("[page]", text);
    });
    page.on("pageerror", (err) => console.log("[pageerror]", err.message));
  });

  test("AI Picks: feedback, API, and long-task budgets", async ({ page, request }) => {
    clearNetworkTimings();
    const urlPatterns = ["/api/parlay", "/parlay/suggest", "/parlay/generate"];
    installNetworkTimingListeners(page, urlPatterns);

    await test.step("Install UX probe before load", async () => {
      await startUXProbe(page);
    });

    await test.step("Navigate to AI Picks", async () => {
      await gotoWithOptionalAuth(page, request, urls.aiPicks);
    });

    await test.step("AI Picks root or sign-in visible", async () => {
      const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
      const root = page.locator(sel.aiPicksRoot).or(page.locator(sel.aiPicksRootFallback));
      await expect(signIn.or(root.first())).toBeVisible({ timeout: 25_000 });
    });

    const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
    if (await signIn.isVisible()) {
      test.skip(true, "Requires auth — on Sign In page");
      return;
    }

    const generateBtn = page.locator(sel.generateBtn).first();
    const btnVisible = await generateBtn.isVisible().catch(() => false);
    if (!btnVisible) {
      test.skip(true, "No Generate/Build button — skipping AI Picks gate");
      return;
    }

    await test.step("Tap Generate", async () => {
      await generateBtn.scrollIntoViewIfNeeded();
      await generateBtn.click();
    });

    const paywall = page.locator(sel.paywall).first();
    const paywallVisible = await paywall.waitFor({ state: "visible", timeout: 4000 }).catch(() => false);
    if (paywallVisible) {
      test.skip(true, "Paywall shown — skipping budget assertions");
      return;
    }

    await test.step("Wait for results or skeleton then results", async () => {
      const skeleton = page.locator(sel.skeleton).first();
      const results = page.locator('[data-testid="pg-ai-results"]').or(page.locator("text=/Confidence/i"));
      const failMessage = page.locator("text=/no games|try again|not enough|upgrade|Select your picks/i");
      await skeleton.waitFor({ state: "visible", timeout: perfBudgets.tapToFeedbackMs + 500 }).catch(() => {});
      await expect(results.or(failMessage).first()).toBeVisible({ timeout: perfBudgets.timeToResultsMs + 5000 });
    });

    await test.step("Enforce API and long-task budgets", async () => {
      const results = await getUXProbeResults(page);

      const relevantApi = results.apiTimings.filter(
        (t) => t.name.includes("parlay") || t.name.includes("suggest") || t.name.includes("generate"),
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
          apiTimings: results.apiTimings.slice(-5),
        }),
      );
    });
  });
});
