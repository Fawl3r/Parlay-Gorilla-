"use client"

import type { SportSlug } from "@/components/games/gamesConfig"
import { getSportBreakInfo } from "@/components/games/sportBreakConfig"
import type { GamesListMeta } from "@/components/games/useGamesForSportDate"

type Props = {
  sport: SportSlug
  sportName: string
  listMeta: GamesListMeta | null
}

export function UpcomingGamesNoGamesState({ sport, sportName, listMeta }: Props) {
  return (
    <div className="text-center py-20">
      <div className="text-gray-200 font-semibold mb-2">No games scheduled.</div>
      {listMeta?.status_label && (
        <div className="text-sm text-gray-200">{listMeta.status_label}</div>
      )}
      {(() => {
        const state = listMeta?.sport_state
        const nextAt = listMeta?.next_game_at
        const daysToNext = listMeta?.days_to_next ?? 0
        const enableDays = listMeta?.preseason_enable_days ?? 14
        if (state === "OFFSEASON" && nextAt) {
          return (
            <div className="text-sm text-gray-200 mt-1">
              Returns{" "}
              {new Date(nextAt).toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
                year: "numeric",
              })}
            </div>
          )
        }
        if (state === "PRESEASON" && nextAt) {
          const startDate = new Date(nextAt).toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
            year: "numeric",
          })
          const unlocksIn =
            daysToNext > 0 && enableDays > 0 && daysToNext > enableDays
              ? daysToNext - enableDays
              : null
          return (
            <>
              <div className="text-sm text-gray-200 mt-1">Preseason starts {startDate}</div>
              {unlocksIn != null && unlocksIn > 0 && (
                <div className="text-sm text-gray-200">Unlocks in {unlocksIn} days</div>
              )}
            </>
          )
        }
        const breakInfo = getSportBreakInfo(sport)
        if (breakInfo) {
          return (
            <div className="text-sm text-gray-200 mt-1">
              {sportName} on {breakInfo.breakLabel} — next games {breakInfo.nextGamesDate}
            </div>
          )
        }
        return null
      })()}
    </div>
  )
}

