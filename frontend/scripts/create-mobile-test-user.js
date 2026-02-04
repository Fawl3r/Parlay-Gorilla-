/**
 * One-time setup: create the mobile E2E test account via the backend register API.
 * Run from frontend dir: npm run test:mobile:create-user
 *
 * Env (frontend/.env.local):
 *   PG_MOBILE_TEST_EMAIL=your-test@example.com
 *   PG_MOBILE_TEST_PASSWORD=YourSecurePassword1!
 *   PG_BACKEND_URL or PG_MOBILE_BACKEND_URL — optional; for prod, defaults to
 *     https://www.parlaygorilla.com (same as test:mobile:login and Playwright).
 *
 * If the user already exists, register returns 400; use the same credentials
 * for npm run test:mobile and npm run test:mobile:login.
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

if (
  PROD_BASE_URL.includes("parlaygorilla.com") &&
  !process.env.PG_MOBILE_BACKEND_URL &&
  !process.env.PG_BACKEND_URL
) {
  backendUrl = PROD_BASE_URL;
}

backendUrl = backendUrl.replace(/\/$/, "");
const email = process.env.PG_MOBILE_TEST_EMAIL;
const password = process.env.PG_MOBILE_TEST_PASSWORD;

if (!email || !password) {
  console.error("Set in frontend/.env.local:");
  console.error("  PG_MOBILE_TEST_EMAIL=your-test@example.com");
  console.error("  PG_MOBILE_TEST_PASSWORD=YourSecurePassword1!");
  process.exit(1);
}

async function main() {
  const url = `${backendUrl}/api/auth/register`;
  console.log("Register URL:", url);
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
  } catch {
    data = {};
  }

  if (res.ok) {
    console.log("OK — Test account created:", email);
    console.log("Run: npm run test:mobile:login (verify) then npm run test:mobile");
    return;
  }

  if (
    res.status === 400 &&
    (data.detail?.includes("already") || (typeof data.detail === "string" && data.detail.includes("already")) || text.includes("already"))
  ) {
    console.log("Account already exists:", email);
    console.log("Use same credentials for npm run test:mobile and npm run test:mobile:login.");
    return;
  }

  console.error("Register failed:", res.status, text.slice(0, 400));
  process.exit(1);
}

main();
