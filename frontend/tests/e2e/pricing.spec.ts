import { test, expect } from "@playwright/test"

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified"

test.beforeEach(async ({ page }) => {
  await page.addInitScript((key: string) => {
    localStorage.setItem(key, "true")
  }, AGE_VERIFIED_KEY)
})

test.describe("Pricing page (public)", () => {
  test("Pricing is public and renders the plan table", async ({ page }) => {
    await page.goto("/pricing")

    await expect(page.locator("[data-age-gate]")).toHaveCount(0)
    await expect(page.locator("[data-testid='pricing-page']")).toBeVisible()

    await expect(page.getByRole("heading", { name: /pricing/i })).toBeVisible()
    await expect(page.locator("[data-testid='pricing-table']")).toBeVisible()

    await expect(page.getByRole("button", { name: /monthly \(card\)/i })).toBeVisible()
    await expect(page.getByRole("button", { name: /continue free/i })).toBeVisible()
  })

  test("/premium redirects to /pricing", async ({ page }) => {
    await page.goto("/premium")

    await expect(page.locator("[data-age-gate]")).toHaveCount(0)
    await expect(page).toHaveURL(/\/pricing\/?(\?.*)?$/)
    await expect(page.getByRole("heading", { name: /pricing/i })).toBeVisible()
  })
})


