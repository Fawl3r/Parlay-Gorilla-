/**
 * Monetization Timing — constants only.
 * Weights and thresholds for intent score and upgrade surfaces.
 */

export const INTENT_WEIGHTS = {
  analysis_view: 2,
  builder_interaction: 3,
  return_visit: 5,
  blurred_pick_seen: 2,
  multi_sport_usage: 4,
  streak_day: 3,
} as const

export const INTENT_LEVEL_THRESHOLDS = {
  exploring: { min: 0, max: 10 },
  engaged: { min: 11, max: 25 },
  powerUser: { min: 26, max: 45 },
  highIntent: { min: 46, max: Infinity },
} as const

export type IntentLevel = keyof typeof INTENT_LEVEL_THRESHOLDS

export const COOLDOWN_MS = 24 * 60 * 60 * 1000 // 24 hours after dismissal

export const SESSION_PROMPT_KEY = "pg_mt_session_prompt_shown"
export const SESSION_LAST_PROMPT_TYPE_KEY = "pg_mt_last_prompt_type"
