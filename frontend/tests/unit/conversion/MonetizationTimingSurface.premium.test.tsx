import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it } from "vitest"
import { MonetizationTimingSurface } from "@/components/conversion/MonetizationTimingSurface"

/**
 * Premium gating: premium users must never see upgrade surfaces.
 */
describe("MonetizationTimingSurface premium gating", () => {
  it("renders nothing when isPremium is true", () => {
    const html = renderToStaticMarkup(
      <MonetizationTimingSurface
        context="after_analysis"
        visible={true}
        isPremium={true}
        authResolved={true}
      />
    )
    expect(html).not.toContain("Learn More")
    expect(html).not.toContain("View Plans")
    expect(html).not.toContain("Unlock deeper")
    expect(html).not.toContain("Premium unlocks")
    expect(html).not.toContain("Ready to access")
    expect(html.trim()).toBe("")
  })

  it("renders nothing when authResolved is false", () => {
    const html = renderToStaticMarkup(
      <MonetizationTimingSurface
        context="after_analysis"
        visible={true}
        isPremium={false}
        authResolved={false}
      />
    )
    expect(html).not.toContain("Learn More")
    expect(html).not.toContain("View Plans")
    expect(html.trim()).toBe("")
  })
})
