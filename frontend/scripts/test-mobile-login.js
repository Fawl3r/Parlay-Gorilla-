/**
 * Verify mobile E2E login works with PG_MOBILE_TEST_* credentials.
 * Run from frontend dir: npm run test:mobile:login
 *
 * Uses same URL logic as playwright.mobile.config.ts:
 * - PROD_BASE_URL or https://www.parlaygorilla.com for prod
 * - PG_MOBILE_BACKEND_URL / PG_BACKEND_URL for API base
 */

try {
  require("dotenv").config({ path: ".env.local" });
  require("dotenv").config({ path: ".env" });
} catch (_) {}

const PROD_BASE_URL =
  process.env.PROD_BASE_URL || "https://www.parlaygorilla.com";

let backendUrl =
  process.env.PG_MOBILE_BACKEND_URL ||
  process.env.PG_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

if (PROD_BASE_URL.includes("parlaygorilla.com") && !process.env.PG_MOBILE_BACKEND_URL && !process.env.PG_BACKEND_URL) {
  backendUrl = PROD_BASE_URL;
}

backendUrl = backendUrl.replace(/\/$/, "");
const email = process.env.PG_MOBILE_TEST_EMAIL;
const password = process.env.PG_MOBILE_TEST_PASSWORD;

async function main() {
  if (!email || !password) {
    console.error("Missing credentials. Set in frontend/.env.local:");
    console.error("  PG_MOBILE_TEST_EMAIL=your-test@example.com");
    console.error("  PG_MOBILE_TEST_PASSWORD=YourPassword");
    process.exit(1);
  }

  const url = `${backendUrl}/api/auth/login`;
  console.log("Login URL:", url);
  console.log("Email:", email);

  let res;
  let text;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    text = await res.text();
  } catch (err) {
    console.error("Request failed:", err.message);
    if (err.cause) console.error("Cause:", err.cause.message);
    process.exit(1);
  }

  let data = {};
  try {
    data = JSON.parse(text);
  } catch (_) {}

  if (res.ok) {
    const token = data.access_token;
    if (token) {
      console.log("OK — Login succeeded.");
      console.log("Token prefix:", token.slice(0, 20) + "...");
      console.log("Mobile tests will use this token when running npm run test:mobile.");
      return;
    }
    console.error("OK response but no access_token in body:", text.slice(0, 200));
    process.exit(1);
  }

  if (res.status === 401) {
    console.error("401 Unauthorized — Wrong email or password, or account not found.");
    console.error("Detail:", data.detail || text);
    process.exit(1);
  }

  if (res.status >= 400) {
    console.error("Login failed:", res.status, text.slice(0, 300));
    process.exit(1);
  }

  console.error("Unexpected response:", res.status, text.slice(0, 200));
  process.exit(1);
}

main();
