import type { KeyPlayer, KeyPlayersBlock } from "@/lib/api"
import type { KeyPlayersViewModel } from "../AnalysisDetailViewModel"

const VERIFIED_LABEL = "Verified current rosters"
const LIMITED_NOTE = "Based on current rosters and roles (limited stat context)."

export function buildKeyPlayersViewModel(params: {
  keyPlayers: KeyPlayersBlock
  redactionCount?: number | null
}): KeyPlayersViewModel {
  const { keyPlayers, redactionCount = 0 } = params
  const players = keyPlayers.players ?? []
  const homePlayers = players.filter((p) => p.team === "home")
  const awayPlayers = players.filter((p) => p.team === "away")
  const verifiedLabel = VERIFIED_LABEL
  const limitedNote =
    keyPlayers.status === "limited" ? LIMITED_NOTE : undefined
  const showRosterVerifiedNote = (redactionCount ?? 0) > 0
  return {
    status: keyPlayers.status,
    reason: keyPlayers.reason,
    homePlayers,
    awayPlayers,
    verifiedLabel,
    limitedNote,
    showRosterVerifiedNote,
    updatedAt: keyPlayers.updated_at,
  }
}
