"use client"

import Link from "next/link"

import { cn } from "@/lib/utils"

type ToolLink = {
  href: string
  title: string
  description: string
}

const TOOL_LINKS: ToolLink[] = [
  {
    href: "/tools/upset-finder",
    title: "Upset Finder",
    description: "Scan matchups for potential volatility and value signals.",
  },
  {
    href: "/tools/odds-heatmap",
    title: "Odds Heatmap",
    description: "Compare spreads/totals at a glance across games.",
  },
  {
    href: "/social",
    title: "Social Feed",
    description: "Browse community picks and discussion.",
  },
  {
    href: "/parlays/history",
    title: "History",
    description: "Review saved results and past activity.",
  },
]

export function InsightsToolsSection({ className }: { className?: string }) {
  return (
    <section className={cn("mt-10", className)} aria-label="Tools">
      <h2 className="text-lg font-black text-white">Tools</h2>
      <p className="mt-1 text-sm text-white/92">Quick shortcuts to secondary destinations (kept out of the navbar).</p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {TOOL_LINKS.map((t) => (
          <Link
            key={t.href}
            href={t.href}
            className={cn(
              "rounded-2xl border border-white/10 bg-white/[0.03] hover:bg-white/[0.06] transition-colors",
              "p-5 block"
            )}
          >
            <div className="text-white font-black">{t.title}</div>
            <div className="mt-1 text-sm text-white/92">{t.description}</div>
          </Link>
        ))}
      </div>
    </section>
  )
}

export default InsightsToolsSection





