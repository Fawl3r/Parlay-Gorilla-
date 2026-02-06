import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it } from "vitest"

import { ConfidenceSection } from "@/components/analysis/detail/ConfidenceSection"

describe("ConfidenceSection", () => {
  it("renders locked card for free users", () => {
    const html = renderToStaticMarkup(
      <ConfidenceSection isPremium={false} analysisContent={{ opening_summary: "" }} />
    )
    expect(html).toContain("Unlock Confidence")
    expect(html).toContain("Pro")
  })

  it("renders unavailable card for premium when confidence not available", () => {
    const html = renderToStaticMarkup(
      <ConfidenceSection
        isPremium={true}
        analysisContent={{
          opening_summary: "",
          confidence: {
            confidence_available: false,
            confidence_score: null,
            components: null,
            blockers: ["market_data_unavailable"],
          },
        }}
      />
    )
    expect(html).toContain("Unavailable")
    expect(html).toContain("be calculated")
    expect(html).toContain("Market data unavailable")
  })

  it("renders breakdown meter for premium when confidence available", () => {
    const html = renderToStaticMarkup(
      <ConfidenceSection
        isPremium={true}
        analysisContent={{
          opening_summary: "",
          confidence: {
            confidence_available: true,
            confidence_score: 65,
            components: {
              market_agreement: 15,
              statistical_edge: 20,
              situational_edge: 10,
              data_quality: 20,
            },
            blockers: [],
          },
        }}
      />
    )
    expect(html).toContain("Confidence Breakdown")
    expect(html).toContain("65%")
  })
})
