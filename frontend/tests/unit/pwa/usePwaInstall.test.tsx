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
      data-has-nudge={String(typeof pwa.nudgeInstallCta === "function")}
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

  it("isIOS when userAgent is iPhone (Safari)", () => {
    vi.stubGlobal("window", {
      matchMedia: () => ({ matches: false }),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })
    vi.stubGlobal("navigator", { userAgent: "iPhone", standalone: false })
    vi.stubGlobal("localStorage", { getItem: vi.fn(() => null), setItem: vi.fn() })
    vi.stubGlobal("sessionStorage", { getItem: vi.fn(() => null), setItem: vi.fn() })
    const html = renderToStaticMarkup(<TestWrapper />)
    vi.unstubAllGlobals()
    expect(html).toContain('data-is-ios="true"')
  })

  it("isIOS false when userAgent is Chrome on iOS (CriOS)", () => {
    vi.stubGlobal("window", {
      matchMedia: () => ({ matches: false }),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })
    vi.stubGlobal("navigator", { userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.0.0 Mobile/15E148 Safari/604.1", standalone: false })
    vi.stubGlobal("localStorage", { getItem: vi.fn(() => null), setItem: vi.fn() })
    vi.stubGlobal("sessionStorage", { getItem: vi.fn(() => null), setItem: vi.fn() })
    const html = renderToStaticMarkup(<TestWrapper />)
    vi.unstubAllGlobals()
    expect(html).toContain('data-is-ios="false"')
  })
})
