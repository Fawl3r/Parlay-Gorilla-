"use client"

import { Filter, Loader2, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { sportsUiPolicy } from "@/lib/sports/SportsUiPolicy"

export type SportOption = { id: string; label: string }

const SPORTS: SportOption[] = [
  { id: "nfl", label: "NFL" },
  { id: "ncaaf", label: "NCAAF" },
  { id: "nba", label: "NBA" },
  { id: "nhl", label: "NHL" },
  { id: "ncaab", label: "NCAAB" },
  { id: "epl", label: "EPL" },
  { id: "laliga", label: "La Liga" },
  { id: "all", label: "All" },
]

export interface UpsetFinderFiltersProps {
  selectedSport: string
  inSeasonBySport: Record<string, boolean>
  onSportChange: (sport: string) => void
  days: number
  onDaysChange: (days: number) => void
  minEdgePct: number
  onMinEdgePctChange: (pct: number) => void
  maxResults: number
  onMaxResultsChange: (n: number) => void
  onRefresh: () => void
  loading: boolean
  canFetch: boolean
}

export function UpsetFinderFilters({
  selectedSport,
  inSeasonBySport,
  onSportChange,
  days,
  onDaysChange,
  minEdgePct,
  onMinEdgePctChange,
  maxResults,
  onMaxResultsChange,
  onRefresh,
  loading,
  canFetch,
}: UpsetFinderFiltersProps) {
  return (
    <div className="py-4 border-b border-white/5 bg-black/20 rounded-lg px-4">
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Sport:</span>
          {SPORTS.map((sport) => {
            const isComingSoon = sport.id !== "all" && sportsUiPolicy.isComingSoon(sport.id)
            const isDisabled = sport.id !== "all" && inSeasonBySport[(sport.id || "").toLowerCase()] === false || isComingSoon
            const disabledLabel = isComingSoon ? "Coming Soon" : "Not in season"
            return (
              <button
                key={sport.id}
                onClick={() => onSportChange(sport.id)}
                disabled={isDisabled}
                className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-medium uppercase transition-all",
                  selectedSport === sport.id
                    ? "bg-emerald-500 text-black"
                    : isDisabled
                      ? "bg-white/5 text-gray-500 cursor-not-allowed opacity-50"
                      : "bg-white/5 text-gray-400 hover:bg-white/10"
                )}
                title={isDisabled ? disabledLabel : undefined}
              >
                {sport.label}
                {isDisabled ? (
                  <span className="ml-2 text-[10px] font-bold uppercase">{disabledLabel}</span>
                ) : null}
              </button>
            )
          })}
        </div>
        <div className="h-6 w-px bg-white/10" />
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <label className="flex items-center gap-2 text-xs text-gray-500">
            Days:
            <input
              type="number"
              min={1}
              max={30}
              value={days}
              onChange={(e) => onDaysChange(Number(e.target.value))}
              className="w-14 bg-black/40 border border-white/10 rounded px-2 py-1 text-white text-xs"
            />
          </label>
          <label className="flex items-center gap-2 text-xs text-gray-500">
            Min edge:
            <input
              type="number"
              min={0}
              max={25}
              value={minEdgePct}
              onChange={(e) => onMinEdgePctChange(Number(e.target.value))}
              className="w-16 bg-black/40 border border-white/10 rounded px-2 py-1 text-white text-xs"
            />
            %
          </label>
          <label className="flex items-center gap-2 text-xs text-gray-500">
            Max results:
            <input
              type="number"
              min={1}
              max={50}
              value={maxResults}
              onChange={(e) => onMaxResultsChange(Number(e.target.value))}
              className="w-16 bg-black/40 border border-white/10 rounded px-2 py-1 text-white text-xs"
            />
          </label>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={!canFetch || loading}
            className="border-white/20"
          >
            {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
            Force Refresh
          </Button>
        </div>
      </div>
    </div>
  )
}
