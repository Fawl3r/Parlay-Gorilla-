import { test, expect, type APIRequestContext } from "@playwright/test";
import { registerUser } from "./helpers/auth";

const backendUrl = process.env.PG_BACKEND_URL || "http://localhost:8000";

async function completeProfile(request: APIRequestContext, token: string) {
  // Required for many routes (non-exempt) to avoid redirect to /profile/setup.
  await request.post(`${backendUrl}/api/profile/setup`, {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      display_name: "Playwright Test",
      default_risk_profile: "balanced",
      favorite_teams: [],
      favorite_sports: [],
    },
  });
}

test.describe("Credit users (non-premium) blur premium pages", () => {
  test("Upset Finder shows blur overlay for credit users; Custom Builder remains accessible", async ({ page, request }) => {
    const email = `credit-blur-${Date.now()}@test.com`;
    const password = "Passw0rd!";
    const token = await registerUser(request, email, password);
    await completeProfile(request, token);

    await page.addInitScript((t: string) => {
      localStorage.setItem("auth_token", t);
      // Bypass age gate for e2e runs.
      localStorage.setItem("parlay_gorilla_age_verified", "true");
    }, token);

    // Stub billing status to simulate a credit user (non-premium) for UI gating.
    await page.route("**/api/billing/status*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          tier: "free",
          plan_code: null,
          can_use_custom_builder: false,
          can_use_upset_finder: false,
          can_use_multi_sport: false,
          can_save_parlays: false,
          max_ai_parlays_per_day: 3,
          remaining_ai_parlays_today: 0,
          unlimited_ai_parlays: false,
          credit_balance: 10,
          is_lifetime: false,
          subscription_end: null,
        }),
      });
    });

    await page.goto("/tools/upset-finder");
    await expect(page.getByText("Premium Page")).toBeVisible();
    await expect(page.getByRole("link", { name: "Upgrade to Premium" })).toBeVisible();

    await page.goto("/app", { waitUntil: "domcontentloaded" });
    await page.getByRole("button", { name: "Custom Builder" }).click();
    await expect(page.getByText("Premium Subscription Required")).toHaveCount(0);
  });
});


