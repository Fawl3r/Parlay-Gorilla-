import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi } from "vitest"

const defaultReturn = {
  isInstallable: false,
  isInstalled: false,
  isIOS: false,
  shouldShowInstallCta: false,
  dismissedUntil: 0,
  promptInstall: vi.fn(),
  dismiss: vi.fn(),
  nudgeInstallCta: vi.fn(),
}

vi.mock("@/lib/pwa/PwaInstallContext", () => ({
  usePwaInstallContext: vi.fn(() => defaultReturn),
}))

import { usePwaInstallContext } from "@/lib/pwa/PwaInstallContext"
import { PwaInstalledBadge } from "@/components/pwa/PwaInstalledBadge"

describe("PwaInstalledBadge", () => {
  it("renders null when not installed", () => {
    vi.mocked(usePwaInstallContext).mockReturnValue({ ...defaultReturn, isInstalled: false })
    const html = renderToStaticMarkup(<PwaInstalledBadge />)
    expect(html).toBe("")
  })

  it("renders Installed badge when installed", () => {
    vi.mocked(usePwaInstallContext).mockReturnValue({ ...defaultReturn, isInstalled: true })
    const html = renderToStaticMarkup(<PwaInstalledBadge />)
    expect(html).toContain("Installed")
    expect(html).toContain("aria-label")
  })
})
