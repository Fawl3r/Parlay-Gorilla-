/**
 * One-time setup: create the mobile E2E test account via the backend register API.
 * Run from frontend dir. Env vars (or .env.local):
 *
 *   PG_BACKEND_URL=https://your-api.com  (or http://localhost:8000)
 *   PG_MOBILE_TEST_EMAIL=mobile-e2e@yourdomain.com
 *   PG_MOBILE_TEST_PASSWORD=YourSecurePassword1!
 *
 *   npm run test:mobile:create-user
 *
 * If the user already exists, register returns 400; use the same credentials
 * for login in tests (no need to run this again).
 */

try {
  require("dotenv").config({ path: ".env.local" });
  require("dotenv").config({ path: ".env" });
} catch (_) {}

const backendUrl =
  process.env.PG_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";
const email = process.env.PG_MOBILE_TEST_EMAIL;
const password = process.env.PG_MOBILE_TEST_PASSWORD;

if (!email || !password) {
  console.error(
    "Set PG_MOBILE_TEST_EMAIL and PG_MOBILE_TEST_PASSWORD, and optionally PG_BACKEND_URL."
  );
  process.exit(1);
}

async function main() {
  const url = `${backendUrl.replace(/\/$/, "")}/api/auth/register`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = {};
  }

  if (res.ok) {
    console.log("Test account created:", email);
    console.log("Run mobile tests with the same PG_MOBILE_TEST_EMAIL and PG_MOBILE_TEST_PASSWORD.");
    return;
  }

  if (res.status === 400 && (data.detail?.includes("already") || text.includes("already"))) {
    console.log("Account already exists:", email);
    console.log("Use the same credentials for npm run test:mobile.");
    return;
  }

  console.error("Register failed:", res.status, text);
  process.exit(1);
}

main();
