"use client"

import { LeaderboardsPageClient } from "@/app/leaderboards/LeaderboardsPageClient"

/**
 * Performance Rankings (formerly Win Wall): show leaderboards inside the app shell.
 */
export function FeedTab() {
  return (
    <div className="min-h-0 flex flex-col overflow-x-hidden">
      <LeaderboardsPageClient />
    </div>
  )
}
