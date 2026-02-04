/**
 * Diagnostic: fail with a clear message if mobile auth is not working,
 * so we see why tests skip instead of silent skip.
 */
import { test, expect } from "@playwright/test";
import {
  getMobileTestToken,
  hasMobileTestCredentials,
  getBackendUrl,
} from "../helpers/auth";
import { gotoWithOptionalAuth } from "../helpers/wait";
import { urls } from "../helpers/urls";
import { sel } from "../helpers/selectors";

test.describe("Mobile PROD — Auth diagnostic", () => {
  test("Credentials and login work so auth-dependent tests can run", async ({
    page,
    request,
  }, testInfo) => {
    if (testInfo.project.name !== "mobile-iphone-14") {
      test.skip(true, "Auth check runs once per suite (mobile-iphone-14)");
      return;
    }
    const hasCreds = hasMobileTestCredentials();
    if (!hasCreds) {
      throw new Error(
        "PG_MOBILE_TEST_EMAIL and/or PG_MOBILE_TEST_PASSWORD not set in frontend/.env.local (or not loaded in worker). " +
          "Run: npm run test:mobile:create-user then npm run test:mobile:login."
      );
    }

    const token = await getMobileTestToken(request);
    if (!token) {
      throw new Error(
        `Login failed (getMobileTestToken returned null). Backend: ${getBackendUrl()}. ` +
          "Run: npm run test:mobile:login to see the exact error."
      );
    }

    await gotoWithOptionalAuth(page, request, urls.gorillaBuilder);
    const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
    const builder = page.locator(sel.pageCustomBuilder);

    // Wait for client to hydrate and apply auth (read localStorage, call /api/auth/me)
    await builder.waitFor({ state: "visible", timeout: 20_000 }).catch(() => {});

    const signInVisible = await signIn.isVisible().catch(() => false);
    if (signInVisible) {
      throw new Error(
        "Token was set but page still shows Sign In. Possible baseURL/origin mismatch (e.g. www vs non-www). " +
          "baseURL should match the host used for login."
      );
    }

    await expect(builder).toBeVisible({ timeout: 5_000 });
  });
});
