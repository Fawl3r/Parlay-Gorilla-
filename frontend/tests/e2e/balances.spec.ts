import { test, expect, type APIRequestContext } from "@playwright/test"
import { registerUser } from "./helpers/auth"

const backendUrl = process.env.PG_BACKEND_URL || "http://localhost:8000"

async function completeProfile(request: APIRequestContext, token: string) {
  await request.post(`${backendUrl}/api/profile/setup`, {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      display_name: "Playwright Test",
      default_risk_profile: "balanced",
      favorite_teams: [],
      favorite_sports: [],
    },
  })
}

test.describe("Balances + status payload", () => {
  test("billing status includes balances; /app shows Account Command Center", async ({ page, request }) => {
    const email = `balances-${Date.now()}@test.com`
    const password = "Passw0rd!"
    const token = await registerUser(request, email, password)
    await completeProfile(request, token)

    // Assert backend payload contract
    const res = await request.get(`${backendUrl}/api/billing/status`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    expect(res.ok()).toBeTruthy()
    const data = await res.json()
    expect(data.balances).toBeTruthy()
    expect(data.balances).toMatchObject({
      credit_balance: expect.any(Number),
      free_parlays_total: expect.any(Number),
      free_parlays_used: expect.any(Number),
      free_parlays_remaining: expect.any(Number),
      daily_ai_limit: expect.any(Number),
      daily_ai_used: expect.any(Number),
      daily_ai_remaining: expect.any(Number),
      premium_ai_parlays_used: expect.any(Number),
    })

    // Log in the UI (localStorage token) + bypass age gate
    await page.addInitScript((t: string) => {
      localStorage.setItem("auth_token", t)
      localStorage.setItem("parlay_gorilla_age_verified", "true")
    }, token)

    await page.goto("/app", { waitUntil: "domcontentloaded" })
    await expect(page.getByRole("heading", { name: "Your Parlay Gorilla Dashboard" })).toBeVisible()

    // Gauges
    await expect(page.getByText("AI Parlays (Today)")).toBeVisible()
    await expect(page.getByText("Custom AI Parlays (Monthly)")).toBeVisible()
    await expect(page.getByText("Credits Balance")).toBeVisible()

    // Quick actions
    await expect(page.getByText(/Generate AI Parlay/i)).toBeVisible()
    await expect(page.getByText(/View Usage & Performance/i)).toBeVisible()
  })
})


