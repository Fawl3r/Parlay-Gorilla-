"use client"

import { HelpCircle } from "lucide-react"
import { LeaderboardPrivacyCard, type LeaderboardVisibility } from "./LeaderboardPrivacyCard"
import { cn } from "@/lib/utils"

interface PrivacyLeaderboardSectionProps {
  initialVisibility?: LeaderboardVisibility
  onSaved?: (v: LeaderboardVisibility) => void
  className?: string
}

const TOOLTIP =
  "Public: show your display name. Anonymous: appear with a generated alias. Hidden: you won't appear on leaderboards."

export function PrivacyLeaderboardSection({
  initialVisibility,
  onSaved,
  className,
}: PrivacyLeaderboardSectionProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center gap-2">
        <h3 className="text-white font-black">Privacy & Leaderboard Control</h3>
        <span
          className="text-white/50 hover:text-white/70 cursor-help"
          title={TOOLTIP}
          aria-label={TOOLTIP}
        >
          <HelpCircle className="h-4 w-4" />
        </span>
      </div>
      <LeaderboardPrivacyCard initialVisibility={initialVisibility} onSaved={onSaved} />
    </div>
  )
}
