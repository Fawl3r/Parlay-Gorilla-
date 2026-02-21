import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi } from "vitest"

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) =>
      React.createElement("div", props, children),
  },
}))

vi.mock("@/lib/pwa/PwaInstallContext", () => ({
  usePwaInstallNudge: () => ({ nudgeInstallCta: () => undefined }),
}))

vi.mock("@/lib/subscription-context", () => ({
  useSubscription: () => ({
    isPremium: true,
    isCreditUser: false,
    canUseUpsetFinder: true,
    refreshStatus: () => undefined,
  }),
  isPaywallError: () => false,
  getPaywallError: () => null,
}))

vi.mock("@/components/paywall/PaywallModal", () => ({
  PaywallModal: () => null,
}))

vi.mock("@/lib/api", () => ({
  api: {
    listSports: vi.fn(),
    getUpsets: vi.fn(),
  },
}))

import { UpsetFinderView } from "@/app/tools/upset-finder/UpsetFinderView"

describe("UpsetFinderView chatbot panel (SSR)", () => {
  it("renders the Upset Finder Assistant panel", () => {
    const html = renderToStaticMarkup(<UpsetFinderView />)
    expect(html).toContain("Upset Finder Assistant")
    expect(html).toContain("Ask Gorilla Bot")
  })
})

