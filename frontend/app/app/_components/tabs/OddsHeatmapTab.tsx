"use client"

import { OddsHeatmapView } from "@/app/tools/odds-heatmap/OddsHeatmapView"

/**
 * Odds Heatmap rendered inline in the app dashboard (no redirect).
 * OddsHeatmapView uses ToolShell internally for consistent premium layout.
 */
export function OddsHeatmapTab() {
  return (
    <div className="min-h-0 flex flex-col overflow-x-hidden">
      <OddsHeatmapView />
    </div>
  )
}
