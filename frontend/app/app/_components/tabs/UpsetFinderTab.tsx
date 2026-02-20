"use client"

import { UpsetFinderView } from "@/app/tools/upset-finder/UpsetFinderView"

/**
 * Upset Finder rendered inline in the app dashboard (no redirect).
 * UpsetFinderView uses ToolShell internally for consistent premium layout.
 */
export function UpsetFinderTab() {
  return (
    <div className="min-h-0 flex flex-col overflow-x-hidden">
      <UpsetFinderView />
    </div>
  )
}
