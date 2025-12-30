"use client"

import { cn } from "@/lib/utils"

export type MatchupBreakdownCardProps = {
  title: string
  summary: string
  bulletInsights: string[]
  className?: string
}

function safeBullets(items: string[], limit: number): string[] {
  const out: string[] = []
  for (const raw of items) {
    const text = String(raw || "").trim()
    if (!text) continue
    out.push(text)
    if (out.length >= limit) break
  }
  return out
}

export function MatchupBreakdownCard({ title, summary, bulletInsights, className }: MatchupBreakdownCardProps) {
  const bullets = safeBullets(bulletInsights, 3)
  const safeSummary = String(summary || "").trim()

  if (!String(title || "").trim() && !safeSummary && bullets.length === 0) return null

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="text-sm font-extrabold text-white">{title}</div>

      {safeSummary ? (
        <div className="mt-3 rounded-xl border border-white/10 bg-black/25 p-3">
          <div className="text-[11px] uppercase tracking-wide text-white/50">Summary</div>
          <div className="mt-1 text-sm leading-6 text-white/85 whitespace-pre-wrap">{safeSummary}</div>
        </div>
      ) : null}

      {bullets.length > 0 ? (
        <div className="mt-3">
          <div className="text-[11px] uppercase tracking-wide text-white/50">Key Notes</div>
          <div className="mt-2 space-y-2">
            {bullets.map((b, idx) => (
              <div key={idx} className="flex items-start gap-2 text-sm text-white/85">
                <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0" aria-hidden="true" />
                <div className="leading-6">{b}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  )
}


