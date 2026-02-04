import type { Page } from "@playwright/test";
import type { APIRequestContext } from "@playwright/test";
import {
  getMobileTestToken,
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

  await page.goto(path, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
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
      await page.addInitScript(
        (t: string, ageKey: string, authKey: string) => {
          localStorage.setItem(authKey, t);
          localStorage.setItem(ageKey, "true");
        },
        token,
        AGE_VERIFIED_KEY,
        AUTH_TOKEN_KEY,
      );
    }
  } else {
    await page.addInitScript((key: string) => {
      localStorage.setItem(key, "true");
    }, AGE_VERIFIED_KEY);
  }

  await page.goto(path, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
}
