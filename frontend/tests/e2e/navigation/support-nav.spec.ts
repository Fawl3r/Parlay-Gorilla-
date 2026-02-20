import { test, expect, type APIRequestContext } from "@playwright/test"
import { registerUser } from "../helpers/auth"

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified"
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

/** Authenticate via API, complete profile, seed token + age gate (matches balances.spec.ts). */
async function loginAsTestUser(
  page: import("@playwright/test").Page,
  request: APIRequestContext
) {
  const email = `support-nav-${Date.now()}@test.com`
  const password = "Passw0rd!"
  const token = await registerUser(request, email, password)
  await completeProfile(request, token)
  await page.addInitScript(
    (args: { token: string; ageKey: string }) => {
      localStorage.setItem("auth_token", args.token)
      localStorage.setItem(args.ageKey, "true")
    },
    { token, ageKey: AGE_VERIFIED_KEY }
  )
  return token
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript((key: string) => {
    localStorage.setItem(key, "true")
  }, AGE_VERIFIED_KEY)
})

test.describe("Sidebar Support nav and Development News highlight", () => {
  test("A: Logged OUT — no sidebar; top nav has Development News, no Feedback", async ({
    page,
  }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" })

    await expect(page.getByTestId("sidebar-section-support")).toHaveCount(0)

    await expect(
      page.getByRole("link", { name: "Development News" }).first()
    ).toBeVisible()

    const primaryNav = page.getByRole("navigation", { name: "Primary navigation" })
    await expect(primaryNav.getByRole("link", { name: "Feedback" })).toHaveCount(
      0
    )
  })

  test("B: Logged IN — Sidebar Support contains Help, Development News, Feedback (in order)", async ({
    page,
    request,
  }) => {
    await loginAsTestUser(page, request)
    await page.goto("/app", { waitUntil: "domcontentloaded" })

    // Wait for auth to hydrate and dashboard (with sidebar) to show
    await expect(
      page.getByRole("heading", { name: "Your Parlay Gorilla Dashboard" })
    ).toBeVisible()

    const supportSection = page.getByTestId("sidebar-section-support")
    await expect(supportSection).toBeVisible()

    const supportItems = page.locator(
      "[data-testid='sidebar-section-support'] a[data-testid^='sidebar-item-']"
    )
    await expect(supportItems.first()).toBeVisible()

    const labels = await supportItems.evaluateAll((els) =>
      els.map((el) => (el as HTMLElement).textContent?.trim() ?? "")
    )
    expect(labels).toEqual(["Help", "Development News", "Feedback"])
  })

  test("C: Active highlight on /development-news and with query param", async ({
    page,
    request,
  }) => {
    await loginAsTestUser(page, request)
    await page.goto("/development-news", { waitUntil: "domcontentloaded" })

    const supportSection = page.getByTestId("sidebar-section-support")
    await expect(supportSection).toBeVisible()

    const devNewsLink = page.getByTestId("sidebar-item-development-news")
    await expect(devNewsLink).toBeVisible()
    await expect(devNewsLink).toHaveAttribute("aria-current", "page")
    await expect(page.getByTestId("sidebar-item-help")).not.toHaveAttribute(
      "aria-current",
      "page"
    )
    await expect(page.getByTestId("sidebar-item-feedback")).not.toHaveAttribute(
      "aria-current",
      "page"
    )

    await page.goto("/development-news?x=1", { waitUntil: "domcontentloaded" })
    await expect(devNewsLink).toHaveAttribute("aria-current", "page")
  })
})
