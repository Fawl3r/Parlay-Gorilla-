import { test, expect } from "@playwright/test"

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified"

test.beforeEach(async ({ page }) => {
  await page.addInitScript((key: string) => {
    localStorage.setItem(key, "true")
  }, AGE_VERIFIED_KEY)
})

test.describe("Analysis detail (mobile)", () => {
  test("shows Quick Take when analysis exists", async ({ page, request }) => {
    const backendUrl =
      process.env.PG_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || "http://localhost:8000"

    const listRes = await request.get(`${backendUrl}/api/analysis/nfl/upcoming?limit=5`, { timeout: 30_000 })
    test.skip(!listRes.ok(), "Analysis list endpoint not available")

    const items = (await listRes.json()) as any[]
    test.skip(!Array.isArray(items) || items.length === 0, "No analyses present in DB")

    const slug = String(items[0]?.slug || "")
    test.skip(!slug, "No slug returned from list endpoint")

    await page.setViewportSize({ width: 390, height: 844 })

    const normalized = slug.startsWith("/") ? slug.slice(1) : slug
    // Our analysis detail route is `/analysis/{sport}/{gameSlug}`. The list endpoint is sport-specific,
    // so ensure we include the sport prefix when navigating.
    const path = normalized.toLowerCase().startsWith("nfl/") ? `/analysis/${normalized}` : `/analysis/nfl/${normalized}`
    await page.goto(path, { waitUntil: "domcontentloaded" })

    // Matchup visuals (team badge + name) should render in the header.
    const matchupTeams = page.locator('[data-testid="matchup-teams"]')
    await expect(matchupTeams).toBeVisible()

    const quickTake = page.locator('[aria-label="Quick take"]')
    await expect(quickTake).toBeVisible()

    // Sticky bottom action bar (mobile-only) should always be visible.
    const actions = page.locator('[aria-label="Primary actions"]')
    await expect(actions).toBeVisible()
    await expect(actions.getByText("Add to Parlay")).toBeVisible()
    await expect(actions.getByText("Save")).toBeVisible()
  })
})


