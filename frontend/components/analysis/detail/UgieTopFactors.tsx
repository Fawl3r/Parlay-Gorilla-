"use client"

import { cn } from "@/lib/utils"

export type UgieTopFactorsProps = {
  topFactors: string[]
  className?: string
}

function safeBullets(items: string[], limit: number): string[] {
  const out: string[] = []
  for (const raw of items) {
    const text = String(raw ?? "").trim()
    if (!text) continue
    out.push(text)
    if (out.length >= limit) break
  }
  return out
}

export function UgieTopFactors({ topFactors, className }: UgieTopFactorsProps) {
  const bullets = safeBullets(topFactors ?? [], 6)
  if (bullets.length === 0) return null

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="text-sm font-extrabold text-white">Top Factors</div>
      <div className="mt-3 space-y-2">
        {bullets.map((b, idx) => (
          <div key={idx} className="flex items-start gap-2 text-sm text-white/85">
            <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0" aria-hidden="true" />
            <div className="leading-6">{b}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
