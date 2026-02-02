/**
 * User-facing copy for parlay UX. Translates internal reason codes and technical
 * state into human language. Never expose NO_ODDS, OUTSIDE_WEEK, etc. to users.
 * Single source of truth: @/lib/parlay/uxLanguageMap.ts
 */

import {
  TRY_THIS_LABEL as UX_TRY_THIS,
  fallbackStageLabel as uxFallbackStageLabel,
  gamesAvailabilitySummary as uxGamesAvailabilitySummary,
  type UxReasonKey,
} from "./uxLanguageMap"

/** Internal exclusion reason codes (backend). Do not show these in the UI. */
export type InternalExclusionReason = UxReasonKey

/** Map internal reason → short human phrase (for tooltips or "why" only). Never as primary message. */
export function reasonToHumanPhrase(reason: InternalExclusionReason | null): string | null {
  if (!reason) return null
  const map: Record<string, string> = {
    NO_ODDS: "Odds aren't posted yet for enough games",
    OUTSIDE_WEEK: "Most games are outside the selected week",
    STATUS_NOT_UPCOMING: "Games haven't opened yet",
    PLAYER_PROPS_DISABLED: "More picks available with player props",
    ENTITLEMENT_BLOCKED: "",
    NO_GAMES_LOADED: "Games may not have loaded yet",
    FEWER_UNIQUE_GAMES_THAN_LEGS: "Not enough different games for this many picks",
  }
  return map[reason] ?? null
}

/** Single calm headline for "not enough picks" error (default UX). */
export const INSUFFICIENT_HEADLINE = "Not enough good games yet"

/** Calm follow-up line (default UX). */
export const INSUFFICIENT_SUBLINE =
  "This is common early in the week or before odds are posted."

/** Copy for "Try this:" section label. */
export const TRY_THIS_LABEL = UX_TRY_THIS

/** Action-oriented button labels (human-friendly). Use getActionLabel from uxLanguageMap per action id. */
export const ACTION_COPY = {
  ml_only: "Use win-only picks",
  all_upcoming: "Include all upcoming games",
  enable_props: "Include player picks",
  lower_legs: "Use fewer picks",
  single_sport: "Use multiple sports",
} as const

/** Fallback stage → user-visible label. */
export function fallbackStageLabel(stage: string): string {
  return uxFallbackStageLabel(stage)
}

/** Eligibility: describe game availability in plain English. Delegates to UX map. */
export function eligibleGamesSummary(options: {
  uniqueGames: number | undefined
  legCount: number | undefined
  numLegsRequested: number
  sport: string
  includePlayerProps: boolean
  beginnerMode?: boolean
}): string {
  return uxGamesAvailabilitySummary({
    ...options,
    beginnerMode: options.beginnerMode ?? false,
  })
}

/** Triple / Confidence Mode: display label (default). Use uxLanguageMap for beginner variant. */
export const TRIPLE_CONFIDENCE_LABEL = "Triple · Confidence Mode"

/** Triple subtext (default). */
export const TRIPLE_SUBTEXT = "Only shown when we find 3 strong picks"

/** Downgrade card: calm explanation when we returned 2 picks instead of 3. */
export function downgradeExplanation(haveStrong: number | null): string {
  const n = haveStrong ?? 2
  if (n === 2) {
    return "We found 2 strong picks today. We skipped forcing a third."
  }
  return `We found ${n} strong picks. We didn't add a weak pick to fill it out.`
}

/** Downgrade "Try this" line. */
export const DOWNGRADE_TRY_THIS =
  "Try again later for 3 picks, or use 2 picks now."
