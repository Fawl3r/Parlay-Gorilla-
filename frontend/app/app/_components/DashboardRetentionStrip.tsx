"use client"

import { useEffect, useState } from "react"
import {
  getProgression,
  getStreak,
  getLastResearchAsOf,
  recordVisit,
  type ProgressionState,
  type StreakState,
} from "@/lib/retention"

function formatResearchAsOf(iso: string | null): string | null {
  if (!iso) return null
  try {
    const date = new Date(iso)
    const now = new Date()
    const sec = Math.floor((now.getTime() - date.getTime()) / 1000)
    if (sec < 60) return "just now"
    if (sec < 3600) return `${Math.floor(sec / 60)}m ago`
    if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`
    if (sec < 86400 * 2) return "yesterday"
    return `${Math.floor(sec / 86400)}d ago`
  } catch {
    return null
  }
}

export function DashboardRetentionStrip() {
  const [progression, setProgression] = useState<ProgressionState | null>(null)
  const [streak, setStreak] = useState<StreakState | null>(null)
  const [lastResearch, setLastResearch] = useState<string | null>(null)

  useEffect(() => {
    recordVisit()
    setProgression(getProgression())
    setStreak(getStreak())
    setLastResearch(getLastResearchAsOf())
  }, [])

  if (!progression && !streak && !lastResearch) return null

  const researchLabel = lastResearch ? formatResearchAsOf(lastResearch) : null

  return (
    <div className="rounded-lg border border-white/10 bg-black/30 backdrop-blur-sm px-3 py-2 mb-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-white/95">
      {progression && progression.analysesViewedCount > 0 && (
        <span>
          Research Activity · Level {progression.level} — {progression.label}
        </span>
      )}
      {streak && streak.currentStreak > 0 && (
        <span>Research streak: {streak.currentStreak} day{streak.currentStreak === 1 ? "" : "s"}</span>
      )}
      {researchLabel && (
        <span>Last research update: {researchLabel}</span>
      )}
    </div>
  )
}
