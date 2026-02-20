"use client"

import type { UpsetFinderToolsAccess, UpsetFinderToolsMeta } from "@/lib/api/types/tools"

export type UpsetFinderEmptyStateActionId =
  | "unlock"
  | "refresh"
  | "set_sport_all"
  | "set_days_14"
  | "set_min_edge_2"
  | "set_min_edge_1"

export interface UpsetFinderEmptyStateAction {
  id: UpsetFinderEmptyStateActionId
  label: string
}

export interface UpsetFinderEmptyStateModel {
  title: string
  message: string
  actions: UpsetFinderEmptyStateAction[]
}

export class UpsetFinderEmptyStateModelBuilder {
  build(input: {
    access: UpsetFinderToolsAccess | null
    meta: UpsetFinderToolsMeta | null
    candidatesCount: number
    days: number
    minEdgePct: number
  }): UpsetFinderEmptyStateModel {
    const gamesScanned = input.meta?.games_scanned ?? 0
    const gamesWithOdds = input.meta?.games_with_odds ?? 0
    const isLocked = input.access ? !input.access.can_view_candidates : false

    if (isLocked) {
      return {
        title: "Unlock Upset Finder",
        message: "See plus-money underdogs where the model has an edge.",
        actions: [{ id: "unlock", label: "Unlock Premium" }],
      }
    }

    if (gamesScanned === 0) {
      return {
        title: "No upcoming games",
        message: `No upcoming games in the next ${input.days} days.`,
        actions: [
          { id: "set_days_14", label: "Days: 14" },
          { id: "set_sport_all", label: "Switch to ALL" },
          { id: "refresh", label: "Refresh" },
        ],
      }
    }

    if (gamesWithOdds === 0) {
      return {
        title: "Odds not posted yet",
        message: `This sport has no moneyline odds in the next ${input.days} days.`,
        actions: [
          { id: "set_sport_all", label: "Switch to ALL" },
          { id: "set_days_14", label: "Days: 14" },
          { id: "refresh", label: "Refresh" },
        ],
      }
    }

    if (input.candidatesCount === 0) {
      return {
        title: `No candidates match filters`,
        message: `No edges at ${input.minEdgePct}% or higher. Lower min edge or widen the date range.`,
        actions: [
          { id: "set_min_edge_2", label: "Min edge: 2%" },
          { id: "set_min_edge_1", label: "Min edge: 1%" },
          { id: "set_days_14", label: "Days: 14" },
          { id: "refresh", label: "Refresh" },
        ],
      }
    }

    return {
      title: "No Upset Candidates Found",
      message: "Try adjusting your filters or selecting a different sport.",
      actions: [{ id: "refresh", label: "Refresh" }],
    }
  }
}

