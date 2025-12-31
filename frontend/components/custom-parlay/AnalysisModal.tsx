"use client"

import { useEffect, useRef } from "react"
import { motion } from "framer-motion"
import type { CounterLegCandidate, CustomParlayAnalysisResponse } from "@/lib/api"
import { getConfidenceStyles, getOverallStyles } from "@/components/custom-parlay/uiHelpers"
import { ClientPortal } from "@/components/ui/ClientPortal"

function AnalysisPanel({
  title,
  analysis,
}: {
  title: string
  analysis: CustomParlayAnalysisResponse
}) {
  const overallStyles = getOverallStyles(analysis.ai_recommendation)

  return (
    <div className={`rounded-2xl border ${overallStyles.border} bg-gradient-to-br ${overallStyles.bg} p-5`}>
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <h3 className="text-xl font-bold text-white">{title}</h3>
          <p className="text-white/60 text-sm">{analysis.num_legs}-leg ticket</p>
        </div>
        <div className={`text-sm font-bold ${overallStyles.text}`}>{analysis.ai_recommendation.replace(/_/g, " ")}</div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="bg-black/40 rounded-lg p-3 text-center">
          <div className="text-white/60 text-xs">AI Probability</div>
          <div className={`text-xl font-bold ${overallStyles.text}`}>{analysis.combined_ai_probability.toFixed(1)}%</div>
        </div>
        <div className="bg-black/40 rounded-lg p-3 text-center">
          <div className="text-white/60 text-xs">Confidence</div>
          <div className={`text-xl font-bold ${overallStyles.text}`}>{analysis.overall_confidence.toFixed(0)}/100</div>
        </div>
        <div className="bg-black/40 rounded-lg p-3 text-center">
          <div className="text-white/60 text-xs">Parlay Odds</div>
          <div className="text-xl font-bold text-white">{analysis.parlay_odds}</div>
        </div>
        <div className="bg-black/40 rounded-lg p-3 text-center">
          <div className="text-white/60 text-xs">Implied</div>
          <div className="text-xl font-bold text-white/80">{analysis.combined_implied_probability.toFixed(1)}%</div>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        <h4 className="text-white font-bold text-sm">Leg Breakdown</h4>
        <div className="space-y-2">
          {analysis.legs.map((leg, i) => (
            <div key={i} className={`bg-black/30 rounded-lg p-3 border ${getConfidenceStyles(leg.recommendation)}`}>
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-white/60 text-xs truncate">{leg.game}</div>
                  <div className="text-white font-medium truncate">{leg.pick_display}</div>
                </div>
                <div className="text-right">
                  <div className="text-white font-bold">{leg.odds}</div>
                  <div className="text-xs">
                    <span className="text-white/60">AI: </span>
                    <span className={getConfidenceStyles(leg.recommendation).split(" ")[1]}>
                      {leg.ai_probability.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-3 text-xs">
                <span className="text-white/60">
                  Conf: <span className="text-white">{leg.confidence.toFixed(0)}%</span>
                </span>
                <span className="text-white/60">
                  Edge:{" "}
                  <span className={leg.edge >= 0 ? "text-green-400" : "text-red-400"}>
                    {leg.edge >= 0 ? "+" : ""}
                    {leg.edge.toFixed(1)}%
                  </span>
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] uppercase ${getConfidenceStyles(leg.recommendation)}`}>
                  {leg.recommendation}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <div className="bg-black/40 rounded-lg p-3">
          <h5 className="text-white font-bold mb-1">Gorilla&apos;s Take</h5>
          <p className="text-white/80 text-sm whitespace-pre-line">{analysis.ai_summary}</p>
        </div>
        <div className="bg-black/40 rounded-lg p-3">
          <h5 className="text-white font-bold mb-1">Risk Notes</h5>
          <p className="text-white/80 text-sm whitespace-pre-line">{analysis.ai_risk_notes}</p>
        </div>
      </div>
    </div>
  )
}

function CandidateList({ candidates }: { candidates: CounterLegCandidate[] }) {
  if (!candidates?.length) return null

  return (
    <div className="rounded-xl border border-white/10 bg-black/30 p-4">
      <h4 className="text-white font-bold text-sm mb-2">What got flipped (and why)</h4>
      <div className="space-y-2">
        {candidates.map((c, idx) => (
          <div
            key={`${c.game_id}-${idx}`}
            className={`flex items-center justify-between gap-3 rounded-lg border p-3 ${
              c.included ? "border-emerald-500/40 bg-emerald-500/10" : "border-white/10 bg-white/5"
            }`}
          >
            <div className="min-w-0">
              <div className="text-xs text-white/60 truncate">
                {c.market_type.toUpperCase()} • {c.original_pick} → <span className="text-white">{c.counter_pick}</span>
              </div>
              <div className="text-xs text-white/50">
                Edge:{" "}
                <span className={c.counter_edge >= 0 ? "text-green-400" : "text-red-400"}>
                  {c.counter_edge >= 0 ? "+" : ""}
                  {c.counter_edge.toFixed(1)}%
                </span>{" "}
                • AI {c.counter_ai_probability.toFixed(1)}% • Conf {c.counter_confidence.toFixed(0)}%
              </div>
            </div>
            <div className="text-right shrink-0">
              <div className="text-xs text-white/70">{c.counter_odds ?? ""}</div>
              <div className="text-[10px] text-white/50">{c.included ? "IN" : "OUT"}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function CustomParlayAnalysisModal({
  analysis,
  counterAnalysis,
  counterCandidates,
  onClose,
}: {
  analysis: CustomParlayAnalysisResponse
  counterAnalysis?: CustomParlayAnalysisResponse | null
  counterCandidates?: CounterLegCandidate[] | null
  onClose: () => void
}) {
  const contentRef = useRef<HTMLDivElement | null>(null)

  // Lock body scroll when modal is open and ensure content starts at top
  useEffect(() => {
    const originalOverflow = document.body.style.overflow
    const originalPaddingRight = document.body.style.paddingRight
    
    // Lock body scroll
    document.body.style.overflow = "hidden"
    
    // Scroll modal content to top when opened
    if (contentRef.current) {
      contentRef.current.scrollTop = 0
    }

    return () => {
      document.body.style.overflow = originalOverflow
      document.body.style.paddingRight = originalPaddingRight
    }
  }, [])

  return (
    <ClientPortal>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-start justify-center p-4 bg-black/80 backdrop-blur-sm"
        onClick={(e) => {
          // Close modal when clicking backdrop
          if (e.target === e.currentTarget) {
            onClose()
          }
        }}
      >
        <motion.div
          ref={contentRef}
          tabIndex={-1}
          initial={{ scale: 0.95, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.95, opacity: 0, y: 20 }}
          transition={{ duration: 0.2 }}
          className="w-full max-w-6xl mt-8 mb-8 max-h-[calc(100vh-4rem)] overflow-y-auto rounded-2xl border border-white/10 bg-black/70 p-4 sm:p-6"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-white">Parlay Breakdown</h2>
              <p className="text-white/60 text-sm">Original ticket + counter/hedge ticket</p>
            </div>
            <button onClick={onClose} className="text-white/60 hover:text-white text-2xl">
              ✕
            </button>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <AnalysisPanel title="Your Ticket" analysis={analysis} />
            {counterAnalysis ? (
              <AnalysisPanel title="Counter Ticket" analysis={counterAnalysis} />
            ) : (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-6 flex items-center justify-center text-white/60">
                Generate a counter ticket to see the opposite side picks with the best model edge.
              </div>
            )}
          </div>

          {counterCandidates && counterCandidates.length > 0 && (
            <div className="mt-4">
              <CandidateList candidates={counterCandidates} />
            </div>
          )}
        </motion.div>
      </motion.div>
    </ClientPortal>
  )
}




