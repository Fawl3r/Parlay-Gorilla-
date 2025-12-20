import { describe, expect, it } from "vitest"

import { AnalysisSectionTabsStyles } from "@/lib/ui/AnalysisSectionTabsStyles"

describe("AnalysisSectionTabsStyles", () => {
  it("prevents tab labels from shrinking/overlapping on small screens", () => {
    expect(AnalysisSectionTabsStyles.container).toContain("overflow-x-auto")
    expect(AnalysisSectionTabsStyles.tabButtonBase).toContain("shrink-0")
    expect(AnalysisSectionTabsStyles.tabButtonBase).toContain("whitespace-nowrap")
  })
})


