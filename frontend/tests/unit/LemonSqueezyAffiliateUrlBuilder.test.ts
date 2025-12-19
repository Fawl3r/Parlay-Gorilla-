import { describe, expect, it } from "vitest"

import { LemonSqueezyAffiliateUrlBuilder } from "@/lib/lemonsqueezy/LemonSqueezyAffiliateUrlBuilder"

describe("LemonSqueezyAffiliateUrlBuilder", () => {
  it("returns original URL when window is not available", async () => {
    const builder = new LemonSqueezyAffiliateUrlBuilder()
    const url = "https://example.com/checkout"
    await expect(builder.build(url)).resolves.toBe(url)
  })

  it("returns original URL when Lemon.js Affiliate.Build is not available", async () => {
    ;(globalThis as any).window = {}
    const builder = new LemonSqueezyAffiliateUrlBuilder()
    const url = "https://example.com/checkout"
    await expect(builder.build(url)).resolves.toBe(url)
    delete (globalThis as any).window
  })

  it("uses LemonSqueezy.Affiliate.Build(url) when available", async () => {
    ;(globalThis as any).window = {
      LemonSqueezy: {
        Affiliate: {
          Build: (url: string) => `${url}?aff=1234`,
        },
      },
    }

    const builder = new LemonSqueezyAffiliateUrlBuilder()
    const url = "https://example.com/checkout"
    await expect(builder.build(url)).resolves.toBe("https://example.com/checkout?aff=1234")
    delete (globalThis as any).window
  })
})


