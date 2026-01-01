import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi } from "vitest"

vi.mock("next/link", () => {
  return {
    default: ({ href, children, ...props }: any) => React.createElement("a", { href, ...props }, children),
  }
})

import { InscriptionSuccessModal } from "@/components/inscriptions/InscriptionSuccessModal"

describe("InscriptionSuccessModal (SSR smoke)", () => {
  it("renders a Solscan link when open", () => {
    const html = renderToStaticMarkup(
      <InscriptionSuccessModal
        open
        payload={{
          savedParlayId: "p1",
          parlayTitle: "Test Parlay",
          solscanUrl: "https://solscan.io/tx/abc123",
          inscriptionTx: "abc123",
        }}
        onClose={() => {}}
      />
    )

    expect(html).toContain("Parlay Inscribed")
    expect(html).toContain("View on Solscan")
    expect(html).toContain("https://solscan.io/tx/abc123")
  })
})


