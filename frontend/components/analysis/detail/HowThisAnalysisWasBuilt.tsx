"use client"

import { useState } from "react"
import { ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * Expandable "How This Analysis Was Built" — research transparency.
 * Content derived from existing data; no new backend.
 */
export function HowThisAnalysisWasBuilt({ className }: { className?: string }) {
  const [open, setOpen] = useState(false)

  const bullets = [
    "Odds market analysis",
    "Team performance metrics",
    "Recent form modeling",
    "Historical matchup signals",
    "AI evaluation layer",
  ]

  return (
    <section
      className={cn(
        "rounded-xl border border-white/10 bg-black/20 backdrop-blur-sm overflow-hidden",
        className
      )}
      aria-expanded={open}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between gap-2 px-4 py-3 text-left text-sm font-medium text-white/80 hover:text-white/90 hover:bg-white/5 transition-colors"
        aria-controls="how-built-content"
        id="how-built-toggle"
      >
        How This Analysis Was Built
        {open ? (
          <ChevronUp className="h-4 w-4 text-white/50 shrink-0" />
        ) : (
          <ChevronDown className="h-4 w-4 text-white/50 shrink-0" />
        )}
      </button>
      <div
        id="how-built-content"
        role="region"
        aria-labelledby="how-built-toggle"
        className={cn(
          "border-t border-white/10 px-4 py-3 text-xs text-white/60 space-y-1.5",
          !open && "hidden"
        )}
      >
        {bullets.map((item, i) => (
          <div key={i} className="flex items-start gap-2">
            <span className="text-white/40 mt-0.5">•</span>
            <span>{item}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
