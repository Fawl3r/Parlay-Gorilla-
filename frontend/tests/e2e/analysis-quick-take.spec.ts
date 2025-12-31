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

    // The list endpoint can include games that don't have an analysis generated yet.
    // Find the first slug that actually resolves on the detail endpoint.
    let slug = ""
    for (const item of items) {
      const raw = String(item?.slug || "")
      if (!raw) continue

      const normalized = raw.startsWith("/") ? raw.slice(1) : raw
      const gameSlug = normalized.toLowerCase().startsWith("nfl/") ? normalized.slice("nfl/".length) : normalized
      if (!gameSlug) continue

      const detailRes = await request.get(`${backendUrl}/api/analysis/nfl/${gameSlug}`, { timeout: 30_000 })
      if (detailRes.ok()) {
        slug = normalized
        break
      }
    }

    test.skip(!slug, "No generated analyses present in DB")

    await page.setViewportSize({ width: 390, height: 844 })

    const path = slug.toLowerCase().startsWith("nfl/") ? `/analysis/${slug}` : `/analysis/nfl/${slug}`
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


