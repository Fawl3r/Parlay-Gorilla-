"use client"

import { Minus, Plus } from "lucide-react"

import { cn } from "@/lib/utils"

export type KeyDriversListProps = {
  positives: string[]
  risks: string[]
  className?: string
}

function safeList(items: string[], limit: number): string[] {
  const out: string[] = []
  for (const raw of items) {
    const next = String(raw || "").trim()
    if (!next) continue
    out.push(next)
    if (out.length >= limit) break
  }
  return out
}

export function KeyDriversList({ positives, risks, className }: KeyDriversListProps) {
  const pos = safeList(positives, 2)
  const neg = safeList(risks, 1)

  if (pos.length === 0 && neg.length === 0) return null

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="text-sm font-extrabold text-white">Top Factors Driving This Pick</div>
      <div className="mt-3 space-y-2">
        {pos.map((text, idx) => (
          <div key={`pos-${idx}`} className="flex items-start gap-2 text-sm text-white/85">
            <Plus className="h-4 w-4 mt-0.5 text-emerald-400 shrink-0" />
            <div className="leading-6">{text}</div>
          </div>
        ))}
        {neg.map((text, idx) => (
          <div key={`neg-${idx}`} className="flex items-start gap-2 text-sm text-white/85">
            <Minus className="h-4 w-4 mt-0.5 text-amber-300 shrink-0" />
            <div className="leading-6">{text}</div>
          </div>
        ))}
      </div>
    </section>
  )
}


