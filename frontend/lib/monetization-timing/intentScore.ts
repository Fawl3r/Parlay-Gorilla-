"use client"

import type { IntentCounters } from "./intentStorage"
import { INTENT_WEIGHTS, INTENT_LEVEL_THRESHOLDS, type IntentLevel } from "./constants"

/**
 * Compute intent score from counters. Frontend-only; value exists in state only.
 */
export function computeIntentScore(c: IntentCounters): number {
  let score = 0
  score += Math.min(c.analyses_viewed_count, 20) * INTENT_WEIGHTS.analysis_view
  score += Math.min(c.builder_interactions, 15) * INTENT_WEIGHTS.builder_interaction
  score += Math.min(c.return_visits, 10) * INTENT_WEIGHTS.return_visit
  score += Math.min(c.blurred_content_views, 10) * INTENT_WEIGHTS.blurred_pick_seen
  if (c.sports_explored_count >= 2) score += INTENT_WEIGHTS.multi_sport_usage
  score += Math.min(c.consecutive_days_active, 7) * INTENT_WEIGHTS.streak_day
  return score
}

export function getIntentLevel(score: number): IntentLevel {
  if (score >= INTENT_LEVEL_THRESHOLDS.highIntent.min) return "highIntent"
  if (score >= INTENT_LEVEL_THRESHOLDS.powerUser.min) return "powerUser"
  if (score >= INTENT_LEVEL_THRESHOLDS.engaged.min) return "engaged"
  return "exploring"
}

export interface IntentState {
  score: number
  level: IntentLevel
}

export function getIntentState(counters: IntentCounters): IntentState {
  const score = computeIntentScore(counters)
  const level = getIntentLevel(score)
  return { score, level }
}
