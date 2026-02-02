import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi, beforeEach } from "vitest"

const mockDismiss = vi.fn()
const mockPromptInstall = vi.fn().mockResolvedValue("unavailable")

const defaultReturn = {
  isInstallable: false,
  isInstalled: false,
  isIOS: false,
  shouldShowInstallCta: false,
  dismissedUntil: 0,
  promptInstall: mockPromptInstall,
  dismiss: mockDismiss,
}

vi.mock("@/lib/pwa/usePwaInstall", () => ({
  usePwaInstall: vi.fn(() => defaultReturn),
}))

vi.mock("next/image", () => ({
  default: ({ src, alt }: { src: string; alt: string }) =>
    React.createElement("img", { src, alt }),
}))

vi.mock("sonner", () => ({
  toast: { success: vi.fn() },
}))

import { usePwaInstall } from "@/lib/pwa/usePwaInstall"
import { PwaInstallCta } from "@/components/pwa/PwaInstallCta"

describe("PwaInstallCta", () => {
  it("renders null when shouldShowInstallCta is false", () => {
    vi.mocked(usePwaInstall).mockReturnValue({
      ...defaultReturn,
      shouldShowInstallCta: false,
    })
    const html = renderToStaticMarkup(<PwaInstallCta />)
    expect(html).toBe("")
  })

  it("renders Install App when installable", () => {
    vi.mocked(usePwaInstall).mockReturnValue({
      ...defaultReturn,
      isInstallable: true,
      shouldShowInstallCta: true,
    })
    const html = renderToStaticMarkup(<PwaInstallCta />)
    expect(html).toContain("Install App")
    expect(html).toContain("Not now")
  })

  it("renders How to Install when iOS and not installable", () => {
    vi.mocked(usePwaInstall).mockReturnValue({
      ...defaultReturn,
      isIOS: true,
      isInstallable: false,
      shouldShowInstallCta: true,
    })
    const html = renderToStaticMarkup(<PwaInstallCta />)
    expect(html).toContain("How to Install")
    expect(html).toContain("Not now")
  })
})
