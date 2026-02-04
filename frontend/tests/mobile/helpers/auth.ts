import type { APIRequestContext } from "@playwright/test";

// Workers may not inherit env from main; load .env.local so credentials are available
try {
  const path = require("node:path");
  const fs = require("node:fs");
  for (const name of [".env.local", ".env"]) {
    const p = path.resolve(process.cwd(), name);
    if (fs.existsSync(p)) {
      require("dotenv").config({ path: p, quiet: true });
      break;
    }
  }
} catch {
  // ignore
}

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified";
const AUTH_TOKEN_KEY = "auth_token";

function getBackendUrl(): string {
  const url =
    process.env.PG_MOBILE_BACKEND_URL ||
    process.env.PG_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000";
  return url.replace(/\/$/, "");
}

/**
 * Login with PG_MOBILE_TEST_EMAIL / PG_MOBILE_TEST_PASSWORD.
 * Returns access_token or null if credentials not set or login fails.
 */
export async function getMobileTestToken(
  request: APIRequestContext,
): Promise<string | null> {
  const email = process.env.PG_MOBILE_TEST_EMAIL;
  const password = process.env.PG_MOBILE_TEST_PASSWORD;
  if (!email || !password) return null;

  const backendUrl = getBackendUrl();
  const res = await request
    .post(`${backendUrl}/api/auth/login`, {
      data: { email, password },
      timeout: 15_000,
    })
    .catch(() => null);
  if (!res?.ok()) return null;
  const data = (await res.json().catch(() => null)) as { access_token?: string };
  return data?.access_token ?? null;
}

/**
 * Complete profile setup so the app doesn't redirect to /profile/setup.
 */
export async function completeMobileTestProfile(
  request: APIRequestContext,
  token: string,
): Promise<void> {
  const backendUrl = getBackendUrl();
  await request
    .post(`${backendUrl}/api/profile/setup`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        display_name: "Mobile E2E Test",
        default_risk_profile: "balanced",
        favorite_teams: [],
        favorite_sports: [],
      },
    })
    .catch(() => {});
}

export function hasMobileTestCredentials(): boolean {
  return !!(process.env.PG_MOBILE_TEST_EMAIL && process.env.PG_MOBILE_TEST_PASSWORD);
}

export { AGE_VERIFIED_KEY, AUTH_TOKEN_KEY };
