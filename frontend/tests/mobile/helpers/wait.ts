import type { Page } from "@playwright/test";
import type { APIRequestContext } from "@playwright/test";
import {
  getMobileTestToken,
  getBackendUrl,
  completeMobileTestProfile,
  hasMobileTestCredentials,
  AGE_VERIFIED_KEY,
  AUTH_TOKEN_KEY,
} from "./auth";

/**
 * Bypass age gate and navigate to path; wait for layout to settle.
 * Use when no test account credentials are set.
 */
export async function gotoAndStabilize(page: Page, path: string): Promise<void> {
  await page.addInitScript((key: string) => {
    localStorage.setItem(key, "true");
  }, AGE_VERIFIED_KEY);

  await page.goto(path, { waitUntil: "load" });
  await page.waitForTimeout(800);
}

/**
 * E2E gate: require auth. Logs in via API, completes profile, injects token, then navigates.
 * Throws (fails the test) if credentials are missing or login fails.
 * Use for production gate where skipping defeats the point.
 */
export async function gotoWithRequiredAuth(
  page: Page,
  request: APIRequestContext,
  path: string,
): Promise<void> {
  if (!hasMobileTestCredentials()) {
    throw new Error(
      "Gate requires PG_MOBILE_TEST_EMAIL and PG_MOBILE_TEST_PASSWORD. " +
      "Set them in CI secrets and frontend/.env.local for local runs.",
    );
  }
  const token = await getMobileTestToken(request);
  if (!token) {
    throw new Error(
      "Gate auth failed: login with PG_MOBILE_TEST_EMAIL / PG_MOBILE_TEST_PASSWORD returned no token. " +
      "Check credentials and backend /api/auth/login.",
    );
  }
  await completeMobileTestProfile(request, token);
  const baseUrl = getBackendUrl();
  const origin = baseUrl.startsWith("http") ? baseUrl : `https://${baseUrl}`;
  try {
    const url = new URL(origin);
    await page.context().addCookies([
      { name: "access_token", value: token, domain: url.hostname, path: "/" },
    ]);
  } catch {
    // ignore
  }
  await page.addInitScript(
    (t: string, ageKey: string, authKey: string) => {
      localStorage.setItem(authKey, t);
      localStorage.setItem(ageKey, "true");
    },
    token,
    AGE_VERIFIED_KEY,
    AUTH_TOKEN_KEY,
  );
  await page.goto(origin, { waitUntil: "domcontentloaded" });
  await page.evaluate(
    ({ t, ageKey, authKey }: { t: string; ageKey: string; authKey: string }) => {
      localStorage.setItem(authKey, t);
      localStorage.setItem(ageKey, "true");
    },
    { t: token, ageKey: AGE_VERIFIED_KEY, authKey: AUTH_TOKEN_KEY },
  );
  await page.goto(path, { waitUntil: "domcontentloaded", timeout: 45_000 });
  await page.waitForTimeout(3000);
}

/**
 * When PG_MOBILE_TEST_EMAIL and PG_MOBILE_TEST_PASSWORD are set: log in via API,
 * complete profile, inject token + age gate, then goto path.
 * Otherwise: same as gotoAndStabilize (age gate only).
 */
export async function gotoWithOptionalAuth(
  page: Page,
  request: APIRequestContext,
  path: string,
): Promise<void> {
  if (hasMobileTestCredentials()) {
    const token = await getMobileTestToken(request);
    if (token) {
      await completeMobileTestProfile(request, token);
      const baseUrl = getBackendUrl();
      const origin = baseUrl.startsWith("http") ? baseUrl : `https://${baseUrl}`;
      try {
        const url = new URL(origin);
        await page.context().addCookies([
          { name: "access_token", value: token, domain: url.hostname, path: "/" },
        ]);
      } catch {
        // ignore
      }
      await page.addInitScript(
        (t: string, ageKey: string, authKey: string) => {
          localStorage.setItem(authKey, t);
          localStorage.setItem(ageKey, "true");
        },
        token,
        AGE_VERIFIED_KEY,
        AUTH_TOKEN_KEY,
      );
      // Hit origin first so localStorage/cookie are on the right domain, then go to path
      await page.goto(origin, { waitUntil: "domcontentloaded" });
      await page.evaluate(
        ({ t, ageKey, authKey }: { t: string; ageKey: string; authKey: string }) => {
          localStorage.setItem(authKey, t);
          localStorage.setItem(ageKey, "true");
        },
        { t: token, ageKey: AGE_VERIFIED_KEY, authKey: AUTH_TOKEN_KEY },
      );
    }
  } else {
    await page.addInitScript((key: string) => {
      localStorage.setItem(key, "true");
    }, AGE_VERIFIED_KEY);
  }

  await page.goto(path, { waitUntil: "domcontentloaded", timeout: 45_000 });
  // Let client read localStorage and run /api/auth/me so UI reflects auth
  await page.waitForTimeout(3000);
}
