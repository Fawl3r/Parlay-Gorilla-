"use client"

import { useMemo } from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import type { AnalysisEnrichment } from "@/lib/api/types/analysis"
import { AuthorityTooltip } from "@/components/authority/AuthorityTooltip"

export type AnalysisHeaderStripProps = {
  /** AI confidence 0–100 from model_win_probability */
  confidencePercent: number | null | undefined
  /** Enrichment for research depth + data freshness */
  enrichment: AnalysisEnrichment | null | undefined
  /** Optional relative timestamp override (e.g. "2 hours ago") */
  dataFreshnessLabel?: string
  className?: string
}

/** Research depth: 3–4 = HIGH, 2 = MODERATE, 0–1 = LOW (frontend-only from data_quality) */
function getResearchDepth(enrichment: AnalysisEnrichment | null | undefined): "HIGH" | "MODERATE" | "LOW" {
  if (!enrichment?.data_quality) return "LOW"
  const dq = enrichment.data_quality
  let score = 0
  if (dq.has_standings) score += 1
  if (dq.has_team_stats) score += 1
  if (dq.has_form) score += 1
  if (dq.has_injuries) score += 1
  if (score >= 3) return "HIGH"
  if (score === 2) return "MODERATE"
  return "LOW"
}

/** Model status from enrichment.data_quality: Stable | Updating | Limited Data (green/yellow/neutral) */
function getModelStatus(enrichment: AnalysisEnrichment | null | undefined): "Stable" | "Updating" | "Limited Data" {
  if (!enrichment?.data_quality) return "Stable"
  const dq = enrichment.data_quality
  const hasNotes = Array.isArray(dq.notes) && dq.notes.length > 0
  const lowDepth = getResearchDepth(enrichment) === "LOW"
  if (hasNotes || lowDepth) return "Limited Data"
  return "Stable"
}

function getDataFreshness(enrichment: AnalysisEnrichment | null | undefined): string {
  const asOf = enrichment?.as_of
  if (!asOf) return "—"
  try {
    const date = new Date(asOf)
    const now = new Date()
    const sec = Math.floor((now.getTime() - date.getTime()) / 1000)
    if (sec < 60) return "just now"
    if (sec < 3600) return `${Math.floor(sec / 60)}m ago`
    if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`
    if (sec < 604800) return `${Math.floor(sec / 86400)}d ago`
    return date.toLocaleDateString()
  } catch {
    return "—"
  }
}

/** Confidence bar color: 0–40 red, 40–65 amber, 65–100 green */
function confidenceGradient(percent: number): string {
  if (percent <= 40) return "from-red-500 to-red-400"
  if (percent <= 65) return "from-amber-500 to-amber-400"
  return "from-emerald-500 to-emerald-400"
}

export function AnalysisHeaderStrip({
  confidencePercent,
  enrichment,
  dataFreshnessLabel,
  className,
}: AnalysisHeaderStripProps) {
  const depth = useMemo(() => getResearchDepth(enrichment), [enrichment])
  const freshness = dataFreshnessLabel ?? getDataFreshness(enrichment)
  const confidence = confidencePercent != null ? Math.min(100, Math.max(0, Number(confidencePercent))) : null
  const modelStatus = useMemo(() => getModelStatus(enrichment), [enrichment])

  const statusColor =
    modelStatus === "Stable"
      ? "text-emerald-400/90"
      : modelStatus === "Limited Data"
        ? "text-amber-400/90"
        : "text-white/70"

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
      className={cn(
        "glass-analytics flex flex-wrap items-center gap-4 sm:gap-6 p-3 sm:p-4",
        className
      )}
    >
      {/* Model Confidence + bar */}
      <div className="flex flex-col gap-1.5 min-w-[120px]">
        <AuthorityTooltip
          label="Model Confidence"
          content="Probability estimate derived from multi-factor evaluation."
        />
        <div className="flex items-center gap-2">
          <span className="pg-data-nums text-white text-sm sm:text-base">
            {confidence != null ? `${Math.round(confidence)}%` : "—"}
          </span>
          {confidence != null && (
            <div className="flex-1 h-1.5 rounded-full bg-white/10 overflow-hidden min-w-[60px] max-w-[100px]">
              <motion.div
                className={cn("h-full rounded-full bg-gradient-to-r pg-confidence-shimmer", confidenceGradient(confidence))}
                initial={{ width: 0 }}
                animate={{ width: `${confidence}%` }}
                transition={{ duration: 0.6, ease: "easeOut" }}
              />
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-0.5">
        <span className="pg-label text-white/65">Research Depth</span>
        <span className="pg-data-nums text-white text-sm sm:text-base">
          {depth === "HIGH" && "HIGH"}
          {depth === "MODERATE" && "MODERATE"}
          {depth === "LOW" && "LOW"}
        </span>
      </div>

      <div className="flex flex-col gap-0.5">
        <span className="pg-label text-white/65">Data Freshness</span>
        <span className="pg-data-nums text-white text-sm sm:text-base">{freshness}</span>
      </div>

      <div className="flex flex-col gap-0.5">
        <span className="pg-label text-white/65">Model Status</span>
        <span className={cn("pg-data-nums text-sm sm:text-base pg-ai-status-pulse", statusColor)}>
          ● {modelStatus}
        </span>
      </div>
    </motion.div>
  )
}
