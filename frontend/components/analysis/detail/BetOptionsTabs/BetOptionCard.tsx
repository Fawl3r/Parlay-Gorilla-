"use client"

import { cn } from "@/lib/utils"

export type BetOptionCardProps = {
  label: string
  lean: string
  confidenceLevel: "Low" | "Medium" | "High"
  riskLevel: "Low" | "Medium" | "High"
  explanation: string
  className?: string
}

export function BetOptionCard({
  label,
  lean,
  confidenceLevel,
  riskLevel,
  explanation,
  className,
}: BetOptionCardProps) {
  return (
    <div className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-extrabold text-white">{label}</div>
          <div className="mt-2 text-sm text-white/70">
            <span className="font-semibold text-white/85">AI Lean:</span>{" "}
            <span className="font-extrabold text-white">{lean}</span>
          </div>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-[11px] uppercase tracking-wide text-white/50">How sure</div>
          <div className="text-sm font-extrabold text-white">{confidenceLevel}</div>
          <div className="mt-1 text-[11px] uppercase tracking-wide text-white/50">Risk</div>
          <div className="text-sm font-extrabold text-white">{riskLevel}</div>
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-white/10 bg-black/25 p-3">
        <div className="text-[11px] uppercase tracking-wide text-white/50">Explanation</div>
        <div className="mt-1 text-sm leading-6 text-white/85 whitespace-pre-wrap">
          {String(explanation || "").trim() || "No explanation available yet."}
        </div>
      </div>
    </div>
  )
}


