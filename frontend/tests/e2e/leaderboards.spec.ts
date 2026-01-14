import { test, expect } from "@playwright/test"

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified"

test.beforeEach(async ({ page }) => {
  await page.addInitScript((key: string) => {
    localStorage.setItem(key, "true")
  }, AGE_VERIFIED_KEY)
})

test.describe("Leaderboards page (public)", () => {
  test("renders all leaderboard tabs", async ({ page }) => {
    await page.goto("/leaderboards", { waitUntil: "domcontentloaded" })

    await expect(page.locator("[data-age-gate]")).toHaveCount(0)
    await expect(page.getByRole("heading", { name: /leaderboards/i })).toBeVisible()

    await expect(page.getByRole("button", { name: "Verified Winners" })).toBeVisible()
    await expect(page.getByRole("button", { name: "AI Power Users" })).toBeVisible()
    await expect(page.getByRole("button", { name: "Arcade Points" })).toBeVisible()

    // Switch tabs
    await page.getByRole("button", { name: "AI Power Users" }).click()
    await expect(page.getByText("AI Gorilla Parlays Usage Leaderboard")).toBeVisible()

    await page.getByRole("button", { name: "Verified Winners" }).click()
    await expect(page.getByText("🦍 Gorilla Parlay Builder 🦍 Leaderboard (Verified)")).toBeVisible()

    await page.getByRole("button", { name: "Arcade Points" }).click()
    await expect(page.getByText("Arcade Points Leaderboard")).toBeVisible()
  })

  test("arcade points tab shows recent wins feed", async ({ page }) => {
    await page.goto("/leaderboards", { waitUntil: "domcontentloaded" })

    await page.getByRole("button", { name: "Arcade Points" }).click()
    await expect(page.getByText("Arcade Points Leaderboard")).toBeVisible()

    // Check for recent wins section (may be empty if no wins exist)
    const recentWinsSection = page.getByText("Recent Verified Wins")
    // If it exists, it should be visible
    if (await recentWinsSection.count() > 0) {
      await expect(recentWinsSection).toBeVisible()
    }
  })
})


