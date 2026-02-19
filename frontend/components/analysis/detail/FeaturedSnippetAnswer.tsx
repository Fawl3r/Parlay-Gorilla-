"use client"

import { cn } from "@/lib/utils"

export type FeaturedSnippetAnswerProps = {
  matchup: string
  favoredTeam: string
  favoredWinPct: number
  underdogTeam: string
  underdogWinPct: number
  aiConfidencePct?: number
  className?: string
}

function clampPct(value: number): number {
  if (!Number.isFinite(value)) return 0
  return Math.max(0, Math.min(100, Math.round(value)))
}

/**
 * FeaturedSnippetAnswer
 *
 * This block is intentionally "snippet-friendly":
 * - Clear question header
 * - Direct answer in the first paragraph
 * - Concrete numbers (win probability)
 *
 * Google snippets are never guaranteed, but this format + JSON-LD increases eligibility.
 */
export function FeaturedSnippetAnswer({
  matchup,
  favoredTeam,
  favoredWinPct,
  underdogTeam,
  underdogWinPct,
  aiConfidencePct,
  className,
}: FeaturedSnippetAnswerProps) {
  const safeMatchup = String(matchup || "").trim() || "this game"
  const safeFavored = String(favoredTeam || "").trim() || "—"
  const safeUnderdog = String(underdogTeam || "").trim() || "—"

  const favored = clampPct(favoredWinPct)
  const underdog = clampPct(underdogWinPct)
  const aiConfidence = aiConfidencePct !== undefined ? clampPct(aiConfidencePct) : undefined

  return (
    <section
      className={cn(
        "rounded-2xl border border-white/10 bg-black/35 backdrop-blur-sm",
        "p-5",
        className
      )}
      aria-label="Quick answer"
    >
      <h2 className="text-base md:text-lg font-extrabold text-white leading-snug">
        Who will win {safeMatchup}?
      </h2>

      <p className="mt-2 text-sm md:text-base leading-6 text-white/80">
        <strong className="text-white">{safeFavored}</strong> is projected to win with{" "}
        <strong className="text-emerald-300">{favored}%</strong> probability. {safeUnderdog} is at{" "}
        <strong className="text-white">{underdog}%</strong>.
      </p>

      {aiConfidence !== undefined ? (
        <p className="mt-2 text-xs text-white/60" title="Probability estimate derived from multi-factor evaluation.">Model Confidence: {aiConfidence}%</p>
      ) : null}
    </section>
  )
}





