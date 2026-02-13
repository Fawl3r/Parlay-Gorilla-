import type { Page } from "@playwright/test";
import type { APIRequestContext } from "@playwright/test";
import {
  getMobileTestToken,
  getFrontendUrl,
  completeMobileTestProfile,
  hasMobileTestCredentials,
  AGE_VERIFIED_KEY,
  AUTH_TOKEN_KEY,
} from "./auth";

const AGE_COOKIE_NAME = "parlay_gorilla_age_verified";
const AGE_QUERY_PARAM = "age_verified";

/** Path with age_verified=1 for bypass. Use with baseURL in config or full URL. */
export function pathWithAgeParam(path: string): string {
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}${AGE_QUERY_PARAM}=1`;
}

/** Run before first navigation so age gate is bypassed (localStorage + cookie). */
export async function setupAgeGateBypass(page: Page): Promise<void> {
  await page.addInitScript(
    (lsKey: string, cookieName: string) => {
      localStorage.setItem(lsKey, "true");
      document.cookie = `${cookieName}=true; path=/; max-age=31536000; SameSite=Lax`;
    },
    AGE_VERIFIED_KEY,
    AGE_COOKIE_NAME,
  );
}

/** After navigation: dismiss age gate modal if visible. */
export async function dismissAgeGateModalIfPresent(page: Page): Promise<void> {
  const ageGate = page.locator("[data-age-gate]").first();
  if ((await ageGate.count()) === 0 || !(await ageGate.isVisible().catch(() => false))) return;
  const confirmBtn = page
    .locator(
      '[data-age-gate] button:has-text("I\'m 21"), [data-age-gate] button:has-text("I am 21"), [data-age-gate] button:has-text("Enter"), [data-age-gate] button:has-text("Yes"), [data-age-gate] [role="button"]:has-text("21")',
    )
    .first();
  if ((await confirmBtn.count()) > 0) await confirmBtn.click().catch(() => {});
  await page.waitForTimeout(500);
}

/**
 * Bulletproof age gate bypass: localStorage + cookie + query param + modal click.
 * Use for production regression (no auth required). Deterministic timeouts.
 */
export async function gotoAndStabilize(page: Page, path: string): Promise<void> {
  await setupAgeGateBypass(page);
  await page.goto(pathWithAgeParam(path), { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);
  await dismissAgeGateModalIfPresent(page);
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
  const frontendUrl = getFrontendUrl();
  const origin = frontendUrl.startsWith("http") ? frontendUrl : `https://${frontendUrl}`;
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
      const frontendUrl = getFrontendUrl();
      const origin = frontendUrl.startsWith("http") ? frontendUrl : `https://${frontendUrl}`;
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
      // Hit frontend origin so localStorage/cookie are on the right domain, then go to path
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
