"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Lock } from "lucide-react"
import { cn } from "@/lib/utils"
import { trackOnboardingQuickStartClicked } from "@/lib/track-event"

const STORAGE_KEY = "pg_quick_start_seen"

export function getQuickStartSeenStored(): boolean {
  if (typeof window === "undefined") return false
  try {
    return localStorage.getItem(STORAGE_KEY) === "true"
  } catch {
    return false
  }
}

export function setQuickStartSeenStored(): void {
  try {
    localStorage.setItem(STORAGE_KEY, "true")
  } catch {
    // ignore
  }
}

export interface QuickStartPanelProps {
  visible: boolean
  onDismiss: () => void
  onSelectNfl: () => void
  onSelectNba: () => void
  onSelectTriple: () => void
  onSelectAllSports: () => void
  tripleAvailable: boolean
  allSportsEntitled: boolean
}

export function QuickStartPanel({
  visible,
  onDismiss,
  onSelectNfl,
  onSelectNba,
  onSelectTriple,
  onSelectAllSports,
  tripleAvailable,
  allSportsEntitled,
}: QuickStartPanelProps) {
  if (!visible) return null

  const handleNfl = () => {
    trackOnboardingQuickStartClicked("nfl")
    onSelectNfl()
    setQuickStartSeenStored()
    onDismiss()
  }
  const handleNba = () => {
    trackOnboardingQuickStartClicked("nba")
    onSelectNba()
    setQuickStartSeenStored()
    onDismiss()
  }
  const handleTriple = () => {
    trackOnboardingQuickStartClicked("confidence_mode")
    onSelectTriple()
    setQuickStartSeenStored()
    onDismiss()
  }
  const handleAllSports = () => {
    trackOnboardingQuickStartClicked("all_sports")
    onSelectAllSports()
    setQuickStartSeenStored()
    onDismiss()
  }

  return (
    <Card className="mb-6 border-primary/30 bg-primary/5">
      <CardContent className="p-4 sm:p-5">
        <h3 className="text-base font-semibold text-foreground mb-1">Quick Start</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Pick a sport and we&apos;ll build your best picks.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleNfl}
            className="min-h-[40px]"
          >
            NFL Picks
          </Button>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleNba}
            className="min-h-[40px]"
          >
            NBA Picks
          </Button>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleTriple}
            disabled={!tripleAvailable}
            className={cn("min-h-[40px]", !tripleAvailable && "opacity-70")}
            title={!tripleAvailable ? "Not enough strong picks right now" : undefined}
          >
            Confidence Mode (Triple)
          </Button>
          {allSportsEntitled ? (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={handleAllSports}
              className="min-h-[40px]"
            >
              All Sports
            </Button>
          ) : (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled
              className="min-h-[40px] opacity-70"
              title="Premium feature"
            >
              <Lock className="h-3.5 w-3 mr-1.5" />
              All Sports (Premium)
            </Button>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-3">You can always customize later.</p>
      </CardContent>
    </Card>
  )
}
