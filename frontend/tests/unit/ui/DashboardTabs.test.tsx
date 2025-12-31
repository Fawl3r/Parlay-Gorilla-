import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it } from "vitest"
import { BarChart3, Calendar, Target, Zap } from "lucide-react"

import { DashboardTabs, type TabType } from "@/app/app/_components/DashboardTabs"

describe("DashboardTabs (SSR smoke)", () => {
  it("does not render a fixed bottom nav (prevents double-bottom-nav overlap on /app)", () => {
    const tabs = [
      { id: "games" as const, label: "Games", icon: Calendar },
      { id: "ai-builder" as const, label: "AI Picks", icon: Zap },
      { id: "custom-builder" as const, label: "Gorilla Parlay Builder", icon: Target },
      { id: "analytics" as const, label: "Insights", icon: BarChart3 },
    ]

    const html = renderToStaticMarkup(
      <DashboardTabs tabs={tabs} activeTab={"games" satisfies TabType} onChange={() => {}} />
    )

    expect(html).not.toContain("dashboard-bottom-nav")
    expect(html).not.toContain("fixed bottom-0")
  })
})


