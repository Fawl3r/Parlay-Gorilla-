/**
 * UX Language Map — single source of truth for AI Picks user-facing copy.
 * Internal reason → exact UI text. Beginner Mode overrides to simpler language.
 * No backend logic changes; copy layer only.
 */

export type UxReasonKey =
  | "NO_ODDS"
  | "OUTSIDE_WEEK"
  | "STATUS_NOT_UPCOMING"
  | "PLAYER_PROPS_DISABLED"
  | "INSUFFICIENT_STRONG_EDGES"
  | "ENTITLEMENT_BLOCKED"
  | "NO_GAMES_LOADED"
  | "FEWER_UNIQUE_GAMES_THAN_LEGS"
  | string

export interface ReasonCopy {
  title: string
  body: string
  action: string
}

/** Default (non-beginner) copy: internal reason → title, body, action. */
export const UX_REASON_COPY: Record<string, ReasonCopy> = {
  NO_ODDS: {
    title: "Games aren't ready yet",
    body: "Odds haven't been posted for enough games.",
    action: "Use win-only picks",
  },
  OUTSIDE_WEEK: {
    title: "Games are outside your selection",
    body: "Most games are scheduled later than your current selection.",
    action: "Include all upcoming games",
  },
  STATUS_NOT_UPCOMING: {
    title: "Games haven't opened yet",
    body: "Some games don't have picks available yet.",
    action: "Include all upcoming games",
  },
  PLAYER_PROPS_DISABLED: {
    title: "More picks are available",
    body: "You can unlock more options by including player picks.",
    action: "Include player picks",
  },
  INSUFFICIENT_STRONG_EDGES: {
    title: "Not enough strong picks",
    body: "We couldn't find enough high-quality picks right now.",
    action: "Use fewer picks",
  },
  ENTITLEMENT_BLOCKED: {
    title: "Not enough good games yet",
    body: "There aren't enough games available right now to build this parlay.",
    action: "Use fewer picks",
  },
  NO_GAMES_LOADED: {
    title: "Not enough good games yet",
    body: "There aren't enough games available right now to build this parlay.",
    action: "Try again",
  },
  FEWER_UNIQUE_GAMES_THAN_LEGS: {
    title: "Not enough strong picks",
    body: "We couldn't find enough high-quality picks right now.",
    action: "Use fewer picks",
  },
}

/** Fallback when reason is unknown (default UX). */
export const UX_REASON_FALLBACK: ReasonCopy = {
  title: "Not enough good games yet",
  body: "There aren't enough games available right now to build this parlay.",
  action: "Use fewer picks",
}

/** Beginner Mode: single calm message. Always use DEFAULT when beginner is ON. */
export const UX_REASON_COPY_BEGINNER: { DEFAULT: ReasonCopy } = {
  DEFAULT: {
    title: "Not enough games yet",
    body: "This usually fixes itself as game day gets closer.",
    action: "Use fewer picks",
  },
}

/** Primary status: when everything works. */
export const STATUS_PICKS_READY = {
  title: "Your picks are ready",
  subtext: "These are the best picks available right now.",
}

/** Not enough games (default). */
export const STATUS_NOT_ENOUGH_GAMES = {
  title: "Not enough good games yet",
  body: "There aren't enough games available right now to build this parlay.",
  secondary: "This is common early in the week or before odds are posted.",
}

/** Not enough games (beginner). */
export const STATUS_NOT_ENOUGH_GAMES_BEGINNER = {
  title: "We couldn't build that right now",
  body: "There aren't enough games available yet. This usually fixes itself as game day gets closer.",
}

/** Triple downgraded to 2 picks — toast. */
export const TRIPLE_DOWNGRADE_TOAST =
  "We found 2 strong picks today. We skipped forcing a third."

/** Triple downgraded — badge. */
export const TRIPLE_DOWNGRADE_BADGE = "Confidence Mode · No forced picks"

/** Fallback used (non-Triple) — info banner. Append fallbackStageLabel for context. */
export const FALLBACK_BANNER =
  "We widened the search to find enough good picks:"

/** Fallback used — tooltip. */
export const FALLBACK_TOOLTIP =
  "We try to stay strict. If the slate is thin, we widen the search instead of forcing weak picks."

/** Fallback (beginner): no mention of filters, eligible, or stages. */
export const FALLBACK_BANNER_BEGINNER =
  "We found the best picks available right now."

/** Triple mode label (default). */
export const TRIPLE_LABEL_DEFAULT = "Triple · Confidence Mode"

/** Triple mode subtext (default). */
export const TRIPLE_SUBTEXT_DEFAULT = "Only shown when we find 3 strong picks"

/** Triple mode label (beginner). */
export const TRIPLE_LABEL_BEGINNER = "Triple · Safer Picks"

/** Triple mode subtext (beginner). */
export const TRIPLE_SUBTEXT_BEGINNER =
  "Only shows up when 3 strong picks are available"

/** Triple tooltip (beginner). */
export const TRIPLE_TOOLTIP_BEGINNER =
  "We won't force picks just to fill a parlay."

/** Triple tooltip (default). */
export const TRIPLE_TOOLTIP_DEFAULT =
  "We only build Triple when we find 3 strong picks — no forced picks."

/** Button labels: human-friendly (default). */
export const BUTTON_LABELS: Record<string, string> = {
  ml_only: "Use win-only picks",
  all_upcoming: "Include all upcoming games",
  lower_legs: "Use fewer picks",
  enable_props: "Include player picks",
  single_sport: "Use multiple sports",
  retry: "Try again",
}

/** Action key to UX map action id (for error quick actions). */
export const ACTION_ID_TO_LABEL_KEY: Record<string, string> = {
  ml_only: "ml_only",
  all_upcoming: "all_upcoming",
  lower_legs: "lower_legs",
  enable_props: "enable_props",
  single_sport: "single_sport",
}

/** Games availability: meaning-based text (no raw numbers when few). */
export function gamesAvailabilitySummary(options: {
  uniqueGames: number | undefined
  legCount: number | undefined
  numLegsRequested: number
  sport: string
  includePlayerProps: boolean
  beginnerMode?: boolean
}): string {
  const { uniqueGames, legCount, numLegsRequested, sport, beginnerMode } =
    options
  const have = uniqueGames ?? legCount ?? 0

  if (beginnerMode) {
    if (have === 0) return "No games available right now."
    if (have < numLegsRequested) return "Some picks are available right now."
    return "Options available right now."
  }

  if (have === 0) {
    return `No games available for ${sport} right now. Try a different sport or include all upcoming games.`
  }
  if (have < numLegsRequested) {
    return "Only a few games are available right now."
  }
  if (have <= 3) {
    return "Only a few games are available right now."
  }
  return "Enough games are available to build your parlay."
}

/** Optional small text under availability (beginner or few games). */
export const AVAILABILITY_HINT =
  "You'll usually see more options closer to game day."

/** "Try this:" section label. */
export const TRY_THIS_LABEL = "Try this:"

/** Get copy for an exclusion reason; respects Beginner Mode. */
export function getCopyForReason(
  reason: UxReasonKey | null,
  beginnerMode: boolean
): ReasonCopy {
  if (beginnerMode) return UX_REASON_COPY_BEGINNER.DEFAULT
  if (!reason || !UX_REASON_COPY[reason]) return UX_REASON_FALLBACK
  return UX_REASON_COPY[reason]
}

/** Get action button label by action id; human-friendly. */
export function getActionLabel(actionId: string): string {
  return BUTTON_LABELS[actionId] ?? actionId.replace(/_/g, " ")
}

/** Reason → action id for single primary action (Beginner Mode uses one button). */
export function getActionIdForReason(reason: UxReasonKey | null, beginnerMode: boolean): string {
  if (beginnerMode) return "lower_legs"
  if (!reason) return "lower_legs"
  const map: Record<string, string> = {
    NO_ODDS: "ml_only",
    OUTSIDE_WEEK: "all_upcoming",
    STATUS_NOT_UPCOMING: "all_upcoming",
    PLAYER_PROPS_DISABLED: "enable_props",
    INSUFFICIENT_STRONG_EDGES: "lower_legs",
    NO_GAMES_LOADED: "lower_legs",
    FEWER_UNIQUE_GAMES_THAN_LEGS: "lower_legs",
    ENTITLEMENT_BLOCKED: "lower_legs",
  }
  return map[reason] ?? "lower_legs"
}

/** Fallback stage → user-visible label (for banner). */
export function fallbackStageLabel(stage: string): string {
  const map: Record<string, string> = {
    week_expanded: "Expanded to all upcoming",
    ml_only: "Win-only picks",
    week_expanded_ml_only: "All upcoming + win-only",
    no_props: "Player picks off",
  }
  return map[stage] ?? stage.replace(/_/g, " ")
}

/** Support ID label (only when error and outside Beginner Mode). Never show "debug ID". */
export const SUPPORT_ID_LABEL = "Support ID:"

/** Support ID tooltip. */
export const SUPPORT_ID_TOOLTIP =
  "Share this with support if you need help."

/** "What happened?" expandable — power users only. */
export const WHAT_HAPPENED_LABEL = "Why?"
export const WHAT_HAPPENED_PRIMARY = "What we saw:"
export const WHAT_HAPPENED_YOU_TRIED = "You tried:"
export const WHAT_HAPPENED_FALLBACK = "Search was widened:"
export const UPDATED_PICK_OPTIONS_TOAST = "Updated pick options"
