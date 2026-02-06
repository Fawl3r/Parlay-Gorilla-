"use client"

import type { GameAnalysisContent } from "@/lib/api/types/analysis"
import { getConfidenceViewState } from "@/lib/analysis/detail/ConfidenceAccessManager"
import { ConfidenceBreakdownMeter } from "./ConfidenceBreakdownMeter"
import { ConfidenceLockedCard } from "@/components/confidence/ConfidenceLockedCard"
import { ConfidenceUnavailableCard } from "@/components/confidence/ConfidenceUnavailableCard"

export type ConfidenceSectionProps = {
  isPremium: boolean
  analysisContent: GameAnalysisContent | null | undefined
  className?: string
}

/**
 * Renders the correct confidence UI: locked (free), unavailable (paid, no data), or full breakdown.
 * Does not render the legacy confidence_breakdown directly; uses confidence result for gating.
 */
export function ConfidenceSection({
  isPremium,
  analysisContent,
  className,
}: ConfidenceSectionProps) {
  const state = getConfidenceViewState(isPremium, analysisContent)

  if (state === "locked") {
    return <ConfidenceLockedCard className={className} />
  }

  if (state === "unavailable") {
    const blockers = analysisContent?.confidence?.blockers ?? []
    return (
      <ConfidenceUnavailableCard
        blockers={blockers as string[]}
        className={className}
      />
    )
  }

  const confidence = analysisContent?.confidence
  if (!confidence?.components || confidence.confidence_score == null) {
    return null
  }
  const breakdownFromResult = {
    market_agreement: confidence.components.market_agreement,
    statistical_edge: confidence.components.statistical_edge,
    situational_edge: confidence.components.situational_edge,
    data_quality: confidence.components.data_quality,
    confidence_total: confidence.confidence_score,
  }
  return (
    <ConfidenceBreakdownMeter
      confidenceBreakdown={breakdownFromResult}
      className={className}
    />
  )
}
