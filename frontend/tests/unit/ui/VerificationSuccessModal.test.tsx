import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it, vi } from "vitest"

vi.mock("next/link", () => {
  return {
    default: ({ href, children, ...props }: any) => React.createElement("a", { href, ...props }, children),
  }
})

import { VerificationSuccessModal } from "@/components/verification/VerificationSuccessModal"

describe("VerificationSuccessModal (SSR smoke)", () => {
  it("renders a viewer link when open", () => {
    const html = renderToStaticMarkup(
      <VerificationSuccessModal
        open
        payload={{
          verificationRecordId: "v1",
          parlayTitle: "Test Parlay",
          viewerUrl: "/verification-records/v1",
          receiptId: "receipt_123",
        }}
        onClose={() => {}}
      />
    )

    expect(html).toContain("Verification created")
    expect(html).toContain("View record")
    expect(html).toContain("/verification-records/v1")
  })
})


