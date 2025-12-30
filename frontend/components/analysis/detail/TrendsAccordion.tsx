"use client"

import { cn } from "@/lib/utils"

export type TrendsAccordionProps = {
  title?: string
  trends: string[]
  className?: string
}

function safeTrends(items: string[], limit: number): string[] {
  const out: string[] = []
  for (const raw of items) {
    const text = String(raw || "").trim()
    if (!text) continue
    out.push(text)
    if (out.length >= limit) break
  }
  return out
}

export function TrendsAccordion({ title = "What History & Context Say", trends, className }: TrendsAccordionProps) {
  const safe = safeTrends(trends, 4)
  if (!safe.length) return null

  return (
    <details className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <summary className="cursor-pointer select-none text-sm font-extrabold text-white">{title}</summary>
      <div className="mt-3 space-y-2">
        {safe.map((t, idx) => (
          <div key={idx} className="flex items-start gap-2 text-sm text-white/85">
            <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-cyan-400 shrink-0" aria-hidden="true" />
            <div className="leading-6">{t}</div>
          </div>
        ))}
      </div>
    </details>
  )
}


