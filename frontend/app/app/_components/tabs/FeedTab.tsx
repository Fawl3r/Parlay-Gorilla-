"use client"

import { LiveMarquee } from "@/components/feed/LiveMarquee"
import { WinWall } from "@/components/feed/WinWall"

export function FeedTab() {
  return (
    <div className="space-y-6">
      <LiveMarquee />
      <WinWall />
    </div>
  )
}
