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

test.describe("Usage & Performance page", () => {
  test("renders key sections for an authenticated user", async ({ page, request }) => {
    const email = `usage-${Date.now()}@test.com`
    const password = "Passw0rd!"
    const token = await registerUser(request, email, password)
    await completeProfile(request, token)

    await page.addInitScript((t: string) => {
      localStorage.setItem("auth_token", t)
      localStorage.setItem("parlay_gorilla_age_verified", "true")
    }, token)

    await page.goto("/usage", { waitUntil: "domcontentloaded" })

    await expect(page.getByRole("heading", { name: "Usage & Performance" })).toBeVisible()
    await expect(page.getByText("This Cycle Overview")).toBeVisible()
    await expect(page.getByText("Usage Breakdown")).toBeVisible()
    await expect(page.getByText("Performance Insights")).toBeVisible()
    await expect(page.getByText("Smart Usage Tips")).toBeVisible()
    await expect(page.getByText("AI Coach Insight")).toBeVisible()
  })
})





