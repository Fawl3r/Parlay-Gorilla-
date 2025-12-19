"use client"

import { BadgeCard } from "./BadgeCard"
import type { BadgeResponse } from "@/lib/api"
import { GlassPanel } from "@/components/ui/glass-panel"

interface BadgeGridProps {
  badges: BadgeResponse[]
  title?: string
  showLocked?: boolean
}

export function BadgeGrid({ badges, title = "Badges", showLocked = true }: BadgeGridProps) {
  const unlockedBadges = badges.filter(b => b.unlocked)
  const lockedBadges = badges.filter(b => !b.unlocked)
  
  const displayBadges = showLocked ? badges : unlockedBadges

  if (displayBadges.length === 0) {
    return (
      <GlassPanel className="text-center">
        <p className="text-gray-500">No badges yet. Start generating parlays to earn badges!</p>
      </GlassPanel>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        <span className="text-sm text-gray-400">
          {unlockedBadges.length} / {badges.length} unlocked
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        {/* Show unlocked badges first */}
        {unlockedBadges.map((badge) => (
          <BadgeCard key={badge.id} badge={badge} size="md" />
        ))}
        
        {/* Show locked badges if enabled */}
        {showLocked && lockedBadges.map((badge) => (
          <BadgeCard key={badge.id} badge={badge} size="md" />
        ))}
      </div>
    </div>
  )
}

