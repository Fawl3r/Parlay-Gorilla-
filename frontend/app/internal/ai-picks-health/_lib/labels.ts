/**
 * Human-readable labels for AI Picks Health dashboard.
 */

export const FAIL_REASON_LABELS: Record<string, string> = {
  NO_ODDS: "Odds not posted yet",
  OUTSIDE_WEEK: "Outside selected week",
  STATUS_NOT_UPCOMING: "Not available yet",
  PLAYER_PROPS_DISABLED: "More options with player picks",
  legacy_422: "Legacy validation",
  unknown: "Other",
  insufficient_candidates: "Not enough candidates",
}

export const QUICK_ACTION_LABELS: Record<string, string> = {
  ml_only: "Win-only picks",
  all_upcoming: "All upcoming",
  enable_props: "Include player picks",
  lower_legs: "Use fewer picks",
  single_sport: "Pick one sport",
}

export function getFailReasonLabel(reason: string): string {
  return FAIL_REASON_LABELS[reason] ?? reason
}

export function getQuickActionLabel(actionId: string): string {
  return QUICK_ACTION_LABELS[actionId] ?? actionId
}
