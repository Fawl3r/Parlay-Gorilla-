import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { usePwaInstall } from "@/lib/pwa/usePwaInstall"

vi.mock("@/lib/track-event", () => ({
  trackEvent: vi.fn(),
}))

function TestWrapper() {
  const pwa = usePwaInstall()
  return (
    <div
      data-should-show={String(pwa.shouldShowInstallCta)}
      data-is-installed={String(pwa.isInstalled)}
      data-is-ios={String(pwa.isIOS)}
      data-is-installable={String(pwa.isInstallable)}
    />
  )
}

describe("usePwaInstall", () => {
  beforeEach(() => {
    vi.stubGlobal("window", undefined)
    vi.stubGlobal("navigator", undefined)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("returns safe defaults in SSR (no window)", () => {
    const html = renderToStaticMarkup(<TestWrapper />)
    expect(html).toContain('data-should-show="false"')
    expect(html).toContain('data-is-installed="false"')
    expect(html).toContain('data-is-installable="false"')
  })

  it("isIOS when userAgent is iPhone", () => {
    vi.stubGlobal("window", {
      matchMedia: () => ({ matches: false }),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })
    vi.stubGlobal("navigator", { userAgent: "iPhone", standalone: false })
    vi.stubGlobal("localStorage", { getItem: vi.fn(() => null), setItem: vi.fn() })
    const html = renderToStaticMarkup(<TestWrapper />)
    vi.unstubAllGlobals()
    expect(html).toContain('data-is-ios="true"')
  })
})
