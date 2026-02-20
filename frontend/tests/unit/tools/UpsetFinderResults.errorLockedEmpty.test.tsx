/**
 * Regression tests: Upset Finder must never show a blank tool.
 * - Paywall/locked state with meta for non-premium
 * - Empty state when candidates empty, with meta counts
 * - Error state on API failure/429 with Retry
 */
import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi } from "vitest"

vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode }) =>
    React.createElement("a", { href, ...props }, children),
}))
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => React.createElement("div", props, children),
  },
}))
vi.mock("@/lib/pwa/PwaInstallContext", () => ({
  usePwaInstallNudge: () => ({ nudgeInstallCta: () => undefined }),
}))

import { UpsetFinderResults } from "@/app/tools/upset-finder/_components/UpsetFinderResults"

const noop = () => undefined

describe("UpsetFinderResults regression: no blank tool", () => {
  it("renders paywall/locked state with meta when user cannot view candidates", () => {
    const html = renderToStaticMarkup(
      <UpsetFinderResults
        candidates={[]}
        meta={{ games_scanned: 10, games_with_odds: 5, missing_odds: 5 }}
        access={{ can_view_candidates: false, reason: "premium_required" }}
        sport="nba"
        days={7}
        minEdgePct={3}
        loading={false}
        error={null}
        onAction={noop}
      />
    )

    expect(html).toContain("Unlock Upset Finder")
    expect(html).toContain("Scanned: 10")
    expect(html).toContain("With odds: 5")
    expect(html).toContain("Unlock Premium")
  })

  it("renders empty state with meta when candidates empty and access allowed", () => {
    const html = renderToStaticMarkup(
      <UpsetFinderResults
        candidates={[]}
        meta={{ games_scanned: 20, games_with_odds: 10, missing_odds: 10 }}
        access={{ can_view_candidates: true, reason: null }}
        sport="nba"
        days={7}
        minEdgePct={4}
        loading={false}
        error={null}
        onAction={noop}
      />
    )

    expect(html).toContain("No candidates match filters")
    expect(html).toContain("Scanned: 20")
    expect(html).toContain("With odds: 10")
    expect(html).toContain("Min edge: 2%")
    expect(html).toContain("Refresh")
  })

  it("renders error state with meta and Retry on API failure", () => {
    const html = renderToStaticMarkup(
      <UpsetFinderResults
        candidates={[]}
        meta={{ games_scanned: 5, games_with_odds: 3, missing_odds: 2 }}
        access={{ can_view_candidates: true, reason: null }}
        sport="nba"
        days={7}
        minEdgePct={3}
        loading={false}
        error="Rate limit exceeded. Try again later."
        onAction={noop}
      />
    )

    expect(html).toContain("Rate limit exceeded")
    expect(html).toContain("Scanned: 5")
    expect(html).toContain("Retry")
  })
})
