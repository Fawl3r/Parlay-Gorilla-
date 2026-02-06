import type { GameAnalysisContent } from "@/lib/api/types/analysis"

export type ConfidenceViewState = "locked" | "unavailable" | "available"

/**
 * Maps subscription + confidence result to UI state.
 * - locked: free user → show ConfidenceLockedCard
 * - unavailable: paid user but confidence_available false → show ConfidenceUnavailableCard
 * - available: paid user and confidence_available true → show ConfidenceBreakdownMeter
 */
export function getConfidenceViewState(
  isPremium: boolean,
  analysisContent: GameAnalysisContent | null | undefined
): ConfidenceViewState {
  if (!isPremium) return "locked"
  const confidence = analysisContent?.confidence
  if (!confidence) return "unavailable"
  if (confidence.confidence_available) return "available"
  return "unavailable"
}
