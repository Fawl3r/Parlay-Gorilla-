import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi } from "vitest"

vi.mock("next/link", () => {
  return {
    default: ({ href, children, ...props }: any) =>
      React.createElement("a", { href, ...props }, children),
  }
})

vi.mock("@/lib/auth-context", () => {
  return {
    useAuth: () => ({
      user: { id: "test-user" },
    }),
  }
})

vi.mock("@/lib/subscription-context", () => {
  return {
    useSubscription: () => ({
      loading: false,
      isPremium: false,
      creditsRemaining: 0,
      freeParlaysUsed: 0,
      freeParlaysTotal: 3,
      freeRemaining: 2,
      todayRemaining: 3,
      todayLimit: 3,
      aiParlaysRemaining: 0,
      aiParlaysLimit: 0,
      customAiParlaysRemaining: 0,
      customAiParlaysLimit: 0,
      inscriptionCostUsd: 0,
      premiumInscriptionsLimit: 0,
      premiumInscriptionsUsed: 0,
      premiumInscriptionsRemaining: 0,
    }),
  }
})

import { BalanceStrip } from "@/components/billing/BalanceStrip"

describe("BalanceStrip (SSR smoke)", () => {
  it("keeps the balances row shrinkable so the Buy Credits CTA can't overlap content", () => {
    const html = renderToStaticMarkup(<BalanceStrip compact />)

    expect(html).toContain("min-w-0")
    expect(html).toContain("flex-1")
    expect(html).toContain("Buy Credits")
  })
})


