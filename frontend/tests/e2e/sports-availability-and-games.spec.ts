import { test, expect } from "@playwright/test"

const MOCK_SPORTS = [
  {
    slug: "nba",
    code: "basketball_nba",
    display_name: "NBA",
    default_markets: ["h2h", "spreads", "totals"],
    in_season: true,
    status_label: "In season",
    sport_state: "IN_SEASON",
    is_enabled: true,
  },
  {
    slug: "mlb",
    code: "baseball_mlb",
    display_name: "MLB",
    default_markets: ["h2h", "spreads", "totals"],
    in_season: false,
    status_label: "Offseason",
    sport_state: "OFFSEASON",
    is_enabled: false,
  },
]

function nextDayIso(): string {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString()
}

function buildMockGamesResponse(nextGameAt: string) {
  const startTime = nextGameAt
  return {
    games: [
      {
        id: "nba-mock-1",
        sport: "nba",
        home_team: "Team A",
        away_team: "Team B",
        start_time: startTime,
        status: "scheduled",
        markets: [],
      },
      {
        id: "nba-mock-2",
        sport: "nba",
        home_team: "Team C",
        away_team: "Team D",
        start_time: startTime,
        status: "scheduled",
        markets: [],
      },
    ],
    next_game_at: nextGameAt,
    sport_state: "IN_SEASON",
    status_label: "In season",
  }
}

test.describe("Sports availability and scheduled games", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("parlay_gorilla_age_verified", "true")
    })
  })

  test("Analysis: disabled sports non-clickable, scheduled games render, Option A banner", async ({
    page,
  }) => {
    const nextAt = nextDayIso()
    const mockGames = buildMockGamesResponse(nextAt)

    await page.route("**/api/sports*", (route) => {
      const url = route.request().url()
      if (url.includes("/games")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockGames),
        })
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_SPORTS),
      })
    })

    await page.goto("/analysis", { waitUntil: "domcontentloaded" })
    await page.waitForLoadState("networkidle").catch(() => {})

    // NBA tab exists and is enabled (clickable)
    const nbaTab = page.getByRole("tab", { name: /NBA/i }).first()
    await expect(nbaTab).toBeVisible()
    await expect(nbaTab).toBeEnabled()
    await expect(nbaTab).not.toHaveAttribute("aria-disabled", "true")

    // MLB tab exists and is disabled
    const mlbTab = page.getByRole("tab", { name: /MLB/i }).first()
    await expect(mlbTab).toBeVisible()
    await expect(mlbTab).toHaveAttribute("disabled", "")
    await expect(mlbTab).toHaveAttribute("aria-disabled", "true")

    // Clicking MLB should not change selection (NBA stays selected or MLB stays disabled)
    await mlbTab.click({ force: true })
    await expect(nbaTab).toBeVisible()

    // Scheduled games render (cards/rows with "Scheduled" status)
    await expect(page.getByText("Scheduled").first()).toBeVisible({ timeout: 5000 })
    await expect(page.getByText("Team A").or(page.getByText("Team B"))).toBeVisible({ timeout: 3000 })

    // Option A banner on Games tab: "No games today — showing next scheduled games (DATE)"
    await page.goto("/app", { waitUntil: "domcontentloaded" })
    await page.waitForLoadState("networkidle").catch(() => {})
    const gamesTab = page.getByRole("button", { name: /Games/i }).or(page.getByRole("tab", { name: /Games/i })).first()
    if (await gamesTab.isVisible()) await gamesTab.click()
    const banner = page.getByText(/No games today.*showing next scheduled games/i)
    await expect(banner).toBeVisible({ timeout: 8000 })
    const nextDate = new Date(nextAt)
    const expectedDateStr = nextDate.toLocaleDateString("en-US", {
      weekday: "long",
      month: "short",
      day: "numeric",
    })
    await expect(page.getByText(expectedDateStr)).toBeVisible()
  })

  test("Parlay Builder: MLB disabled, NBA selectable", async ({ page }) => {
    await page.route("**/api/sports*", (route) => {
      const url = route.request().url()
      if (url.includes("/games")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ games: [], next_game_at: null }),
        })
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_SPORTS),
      })
    })

    await page.goto("/app", { waitUntil: "domcontentloaded" })
    await page.waitForLoadState("networkidle").catch(() => {})

    // Open Gorilla Parlay Builder / AI Picks (sport chips)
    const builderTab = page.getByRole("button", { name: /Gorilla Parlay Builder|AI Picks/i }).first()
    if (await builderTab.isVisible()) {
      await builderTab.click()
    }

    // MLB chip/button should be disabled
    const mlbChip = page.getByRole("button", { name: /MLB/i }).first()
    await expect(mlbChip).toBeVisible({ timeout: 5000 })
    await expect(mlbChip).toBeDisabled()

    // NBA should be selectable (enabled)
    const nbaChip = page.getByRole("button", { name: /NBA/i }).first()
    await expect(nbaChip).toBeVisible()
    await expect(nbaChip).toBeEnabled()
  })

  test("Stale-while-error: cached sports shown with error banner when /api/sports fails", async ({
    page,
  }) => {
    let listCallCount = 0
    await page.route("**/api/sports*", (route) => {
      const url = route.request().url()
      if (url.includes("/games")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ games: [], next_game_at: null }),
        })
      }
      listCallCount++
      if (listCallCount === 1) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(MOCK_SPORTS),
        })
      }
      return route.fulfill({ status: 500, body: "Server error" })
    })

    await page.goto("/analysis", { waitUntil: "domcontentloaded" })
    await page.waitForLoadState("networkidle").catch(() => {})

    await expect(page.getByRole("tab", { name: /NBA/i }).first()).toBeVisible()
    await expect(page.getByRole("tab", { name: /MLB/i }).first()).toBeVisible()

    await page.reload({ waitUntil: "domcontentloaded" })
    await page.waitForLoadState("networkidle").catch(() => {})

    await expect(page.getByRole("tab", { name: /NBA/i }).first()).toBeVisible()
    await expect(page.getByRole("tab", { name: /MLB/i }).first()).toBeVisible()
    await expect(page.getByText("Couldn't reach backend").or(page.getByText("Couldn't reach backend. Try refresh."))).toBeVisible()
    await expect(page.getByText("Showing last saved sports list").first()).toBeVisible({ timeout: 3000 })
  })
})
