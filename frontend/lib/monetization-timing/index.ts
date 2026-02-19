/**
 * Monetization Timing — frontend-only intent tracking and upgrade timing.
 * No backend, no paywalls. Prepares users to want to pay at the right moment.
 */

export {
  recordAnalysisView,
  recordBuilderInteraction,
  recordReturnVisit,
  recordBlurredContentView,
  getIntentCounters,
  isFirstVisit,
  setFirstVisitIfNeeded,
  getDismissal,
} from "./intentStorage"
export type { IntentCounters, IntentDismissal } from "./intentStorage"

export { computeIntentScore, getIntentLevel, getIntentState } from "./intentScore"
export type { IntentState } from "./intentScore"

export {
  isInCooldown,
  hasShownPromptThisSession,
  markPromptShownThisSession,
  getRecommendedSurface,
  canShowInContext,
  recordDismissal,
  getCurrentIntentLevel,
} from "./timingEngine"
export type { UpgradeSurfaceType } from "./timingEngine"

export { emitIntentEvent } from "./intentEvents"
export type { IntentEventType } from "./intentEvents"

export {
  INTENT_WEIGHTS,
  INTENT_LEVEL_THRESHOLDS,
  COOLDOWN_MS,
  SESSION_PROMPT_KEY,
  SESSION_LAST_PROMPT_TYPE_KEY,
} from "./constants"
export type { IntentLevel } from "./constants"
