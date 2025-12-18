import { test, expect } from "@playwright/test";
import { registerUser, adminWalletLogin } from "./helpers/auth";

// Skipped by default; enable when backend + data seed are available.
test.describe.skip("Affiliate + Admin flows", () => {
  test("affiliate journey: register -> join -> dashboard stats fetch", async ({ request, page }) => {
    const email = `aff-${Date.now()}@test.com`;
    const password = "Passw0rd!";
    const token = await registerUser(request, email, password);

    await page.context().addCookies([
      { name: "auth_token", value: token, url: process.env.PG_FRONTEND_URL || "http://localhost:3000" },
    ]);

    await page.goto("/affiliates/dashboard");
    await expect(page.getByText("Affiliate Dashboard")).toBeVisible();
    await expect(page.getByText("Your Referral Link")).toBeVisible();
  });

  test("admin affiliate list renders", async ({ request, page }) => {
    const adminToken = await adminWalletLogin(request, process.env.PG_ADMIN_WALLET || "4E58m1qpnxbFRoDZ8kk9zu3GT6YLrPtPk65u8Xa2ZgBU");

    await page.context().addCookies([
      { name: "admin_token", value: adminToken, url: process.env.PG_FRONTEND_URL || "http://localhost:3000" },
    ]);

    await page.goto("/admin/affiliates");
    await expect(page.getByText("Affiliates")).toBeVisible();
    await expect(page.getByText("Performance by affiliate")).toBeVisible();
  });
});


