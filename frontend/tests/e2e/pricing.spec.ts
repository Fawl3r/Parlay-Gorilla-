import { test, expect } from "@playwright/test"

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified"

test.beforeEach(async ({ page }) => {
  await page.addInitScript((key: string) => {
    localStorage.setItem(key, "true")
  }, AGE_VERIFIED_KEY)
})

test.describe("Pricing page (public)", () => {
  test("Pricing is public and renders tabs", async ({ page }) => {
    await page.goto("/pricing", { waitUntil: "domcontentloaded" })

    await expect(page.locator("[data-age-gate]")).toHaveCount(0)
    await expect(page.locator("[data-testid='pricing-page']")).toBeVisible()

    await expect(page.getByRole("heading", { name: /pricing/i })).toBeVisible()
    await expect(page.locator("[data-testid='pricing-tabs']")).toBeVisible()
    await expect(page.locator("[data-testid='pricing-tab-subscriptions']")).toBeVisible()
    await expect(page.locator("[data-testid='pricing-tab-credits']")).toBeVisible()
  })

  test("Mobile shows sticky CTA bar", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto("/pricing", { waitUntil: "domcontentloaded" })

    await expect(page.locator("[data-age-gate]")).toHaveCount(0)
    await expect(page.locator("[data-testid='pricing-page']")).toBeVisible()
    await expect(page.locator("[data-testid='pricing-sticky-cta']")).toBeVisible()
  })

  test("/premium redirects to /pricing", async ({ page }) => {
    await page.goto("/premium", { waitUntil: "domcontentloaded" })

    await expect(page.locator("[data-age-gate]")).toHaveCount(0)
    await expect(page).toHaveURL(/\/pricing\/?(\?.*)?$/)
    await expect(page.getByRole("heading", { name: /pricing/i })).toBeVisible()
  })
})


