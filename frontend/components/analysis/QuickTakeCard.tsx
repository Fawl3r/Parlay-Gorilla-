"use client"

import { Sparkles } from "lucide-react"

import { cn } from "@/lib/utils"

export function QuickTakeCard({
  summary,
  className,
}: {
  summary: string
  className?: string
}) {
  const text = String(summary || "").trim()
  if (!text) return null

  return (
    <div
      className={cn(
        "rounded-2xl border border-emerald-500/20 bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 p-4",
        className
      )}
      aria-label="Quick take"
    >
      <div className="flex items-center gap-2 text-emerald-300 text-xs font-bold uppercase tracking-wide">
        <Sparkles className="h-4 w-4" />
        Quick take
      </div>
      <details className="mt-2">
        <summary className="cursor-pointer select-none text-sm font-semibold text-white">
          Tap to read the quick summary
        </summary>
        <div className="mt-2 text-sm leading-6 text-gray-200/90 whitespace-pre-wrap">{text}</div>
      </details>
    </div>
  )
}


