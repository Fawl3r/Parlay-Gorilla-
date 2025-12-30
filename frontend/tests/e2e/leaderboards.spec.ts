import { test, expect } from "@playwright/test"

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified"

test.beforeEach(async ({ page }) => {
  await page.addInitScript((key: string) => {
    localStorage.setItem(key, "true")
  }, AGE_VERIFIED_KEY)
})

test.describe("Leaderboards page (public)", () => {
  test("renders both leaderboard tabs", async ({ page }) => {
    await page.goto("/leaderboards", { waitUntil: "domcontentloaded" })

    await expect(page.locator("[data-age-gate]")).toHaveCount(0)
    await expect(page.getByRole("heading", { name: /leaderboards/i })).toBeVisible()

    await expect(page.getByRole("button", { name: "Verified Winners" })).toBeVisible()
    await expect(page.getByRole("button", { name: "AI Power Users" })).toBeVisible()

    // Switch tabs
    await page.getByRole("button", { name: "AI Power Users" }).click()
    await expect(page.getByText("AI Parlay Usage Leaderboard")).toBeVisible()

    await page.getByRole("button", { name: "Verified Winners" }).click()
    await expect(page.getByText("Custom Parlay Leaderboard (On-Chain Verified)")).toBeVisible()
  })
})


