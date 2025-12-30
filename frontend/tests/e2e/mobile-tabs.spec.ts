import { test, expect, type APIRequestContext } from "@playwright/test"
import { registerUser } from "./helpers/auth"

const backendUrl = process.env.PG_BACKEND_URL || "http://localhost:8000"
const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified"

async function completeProfile(request: APIRequestContext, token: string) {
  await request.post(`${backendUrl}/api/profile/setup`, {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      display_name: "Playwright Mobile",
      default_risk_profile: "balanced",
      favorite_teams: [],
      favorite_sports: [],
    },
  })
}

test.describe("Mobile bottom tabs", () => {
  test("shows bottom tabs on /app and highlights active route", async ({ page, request }) => {
    const email = `tabs-${Date.now()}@test.com`
    const password = "Passw0rd!"
    const token = await registerUser(request, email, password)
    await completeProfile(request, token)

    await page.setViewportSize({ width: 390, height: 844 })

    // Bypass AgeGate before first navigation.
    await page.addInitScript((key: string) => {
      localStorage.setItem(key, "true")
    }, AGE_VERIFIED_KEY)

    // Navigate and sign in through UI to ensure AuthProvider hydrates consistently on mobile.
    await page.goto("/auth/login", { waitUntil: "domcontentloaded" })

    // Wait for hydration so controlled inputs don't get reset mid-fill.
    await page.waitForLoadState("networkidle")

    const emailInput = page.locator("input#email")
    const passwordInput = page.locator("input#password")

    // Retry fill once in case React hydration wipes the first attempt.
    for (let attempt = 0; attempt < 2; attempt++) {
      await emailInput.fill(email)
      await passwordInput.fill(password)
      const currentEmail = await emailInput.inputValue()
      if (currentEmail === email) break
      await page.waitForTimeout(150)
    }

    await expect(emailInput).toHaveValue(email)
    await page.getByRole("button", { name: /sign in/i }).click()

    // The login flow should land on /app (or /profile/setup, but we already completed profile).
    await expect(page).toHaveURL(/\/app\/?(\?.*)?$/)

    const nav = page.locator("[data-testid='mobile-bottom-tabs']")
    await expect(nav).toBeVisible()

    const active = nav.locator("a[aria-current='page']")
    await expect(active).toContainText("Home")

    // Navigate to Games tab
    await nav.getByRole("link", { name: "Games" }).click()
    await expect(page).toHaveURL(/\/analysis\/?(\?.*)?$/)
    await expect(nav.locator("a[aria-current='page']")).toContainText("Games")
  })
})


