"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { GlassCard } from "@/components/ui/GlassCard"

export interface ToolShellPill {
  label: string
  value: string
}

export interface ToolShellProps {
  /** Main title (e.g. "Insights", "Odds Heatmap") */
  title: string
  /** Optional subtitle below title */
  subtitle?: string
  /** Optional pills row (e.g. Status, Sport, Last updated) */
  pills?: ToolShellPill[]
  /** Optional left panel (filters, legend). When provided, desktop uses 2-col layout. */
  left?: React.ReactNode
  /** Main content (stats, table, results) */
  right: React.ReactNode
  /** When true, right panel is sticky on lg breakpoint */
  stickyRight?: boolean
  className?: string
}

/**
 * Shared premium tool layout: gradient page, hero with title/subtitle/pills,
 * optional left panel (filters) + right content. Used by Insights, Odds Heatmap, Upset Finder.
 * No data fetching; layout only.
 */
export function ToolShell({
  title,
  subtitle,
  pills,
  left,
  right,
  stickyRight = false,
  className,
}: ToolShellProps) {
  return (
    <div
      className={cn(
        "min-h-0 overflow-x-hidden bg-gradient-to-b from-black via-black/95 to-black/90 rounded-2xl",
        className
      )}
    >
      <section
        className="relative border-b border-green-500/20 px-4 py-5 sm:px-6 rounded-t-2xl"
        aria-hidden={undefined}
      >
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.07] rounded-t-2xl"
          aria-hidden
          style={{
            background:
              "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(34, 197, 94, 0.4), transparent 70%)",
          }}
        />
        <div className="relative">
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-white">
            {title}
          </h1>
          {subtitle != null && subtitle !== "" && (
            <p className="text-sm text-white/60 mt-1">{subtitle}</p>
          )}
          {pills != null && pills.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {pills.map((p) => (
                <span
                  key={p.label}
                  className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-white/80 transition-all duration-150 hover:scale-[1.02]"
                >
                  <span className="text-white/50 mr-1.5">{p.label}:</span>
                  {p.value}
                </span>
              ))}
            </div>
          )}
        </div>
      </section>

      <div className="px-4 sm:px-6 py-4 lg:py-6">
        {left != null ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-6">
            <div className="lg:col-span-4 xl:col-span-3 w-full max-w-[360px] lg:max-w-none">
              <GlassCard className="p-4 h-full">{left}</GlassCard>
            </div>
            <div
              className={cn(
                "lg:col-span-8 xl:col-span-9 min-w-0 flex flex-col",
                stickyRight && "lg:sticky lg:top-4 lg:self-start"
              )}
            >
              <GlassCard variant="strong" className="p-4 flex-1 min-h-0 min-w-0 overflow-x-auto overflow-y-auto">
                {right}
              </GlassCard>
            </div>
          </div>
        ) : (
          <GlassCard variant="strong" className="p-4 min-h-0 min-w-0 overflow-x-auto">
            {right}
          </GlassCard>
        )}
      </div>
    </div>
  )
}
