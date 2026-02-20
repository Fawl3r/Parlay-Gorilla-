"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { GlassCard } from "@/components/ui/GlassCard"

export type BuilderPill = { label: string; value: string }

export type BuilderShellProps = {
  title: string
  subtitle?: string
  pills?: BuilderPill[]
  left: React.ReactNode
  right: React.ReactNode
  primaryAction?: {
    label: string
    onClick: () => void
    loading?: boolean
    disabled?: boolean
  }
  secondaryAction?: {
    label: string
    onClick: () => void
    disabled?: boolean
  }
  /** Optional class for the outer container */
  className?: string
}

/**
 * Premium builder layout: hero header, responsive 2-pane (desktop) / stack (mobile), sticky preview and CTA.
 * No business logic; presentation only.
 */
export function BuilderShell({
  title,
  subtitle,
  pills = [],
  left,
  right,
  primaryAction,
  secondaryAction,
  className,
}: BuilderShellProps) {
  return (
    <div
      className={cn(
        "min-h-0 flex flex-col overflow-x-hidden",
        "bg-gradient-to-b from-black via-black/95 to-black/90",
        className
      )}
      data-testid="builder-shell"
    >
      {/* Hero header: gradient, glow, divider */}
      <section className="relative border-b border-green-500/20 bg-gradient-to-b from-black via-black/95 to-black/90 px-4 py-5 sm:px-6">
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.07]"
          aria-hidden
          style={{
            background: "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(34, 197, 94, 0.4), transparent 70%)",
          }}
        />
        <div className="relative max-w-7xl mx-auto">
          <h1 className="text-2xl sm:text-3xl font-bold text-white">{title}</h1>
          {subtitle && <p className="text-sm text-white/60 mt-1">{subtitle}</p>}
          {pills.length > 0 && (
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

      {/* Main: 2-pane desktop, stack mobile — extra spacing below hero */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 pt-6 pb-4 sm:px-6 sm:pt-8 sm:pb-6 flex flex-col lg:flex-row gap-6 lg:gap-8">
        {/* Left: controls */}
        <div className="lg:w-[min(420px,45%)] lg:shrink-0 flex flex-col gap-4">
          {left}
        </div>

        {/* Right: preview / results — sticky on desktop, stronger blur */}
        <div className="lg:flex-1 lg:min-w-0">
          <div className="lg:sticky lg:top-4">
            <GlassCard variant="strong" className="min-h-[200px] lg:min-h-[280px]">
              {right}
            </GlassCard>
          </div>
        </div>
      </div>

      {/* Sticky bottom CTA bar (mobile only) */}
      {(primaryAction ?? secondaryAction) && (
        <div
          className={cn(
            "lg:hidden fixed bottom-0 left-0 right-0 z-40",
            "border-t border-white/10 bg-black/90 backdrop-blur-md px-4 py-3",
            "safe-area-pb"
          )}
        >
          <div className="max-w-7xl mx-auto flex items-center gap-3">
            {secondaryAction && (
              <button
                type="button"
                disabled={secondaryAction.disabled}
                onClick={secondaryAction.onClick}
                className="px-4 py-2.5 rounded-lg border border-white/20 text-sm font-medium text-white/80 hover:bg-white/10 disabled:opacity-50 transition-all duration-150"
                aria-label={secondaryAction.label}
              >
                {secondaryAction.label}
              </button>
            )}
            {primaryAction && (
              <button
                type="button"
                disabled={primaryAction.disabled || primaryAction.loading}
                onClick={primaryAction.onClick}
                className="flex-1 min-h-[44px] rounded-lg bg-emerald-500 text-black font-semibold text-sm hover:bg-emerald-400 hover:shadow-[0_0_20px_rgba(34,197,94,0.3)] disabled:opacity-50 transition-all duration-150 flex items-center justify-center gap-2"
                aria-label={primaryAction.label}
                aria-busy={primaryAction.loading}
              >
                {primaryAction.loading ? (
                  <>
                    <span className="h-4 w-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                    <span>Loading…</span>
                  </>
                ) : (
                  primaryAction.label
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Spacer so content is not hidden behind sticky bar on mobile */}
      {(primaryAction ?? secondaryAction) && <div className="h-20 lg:hidden" aria-hidden />}
    </div>
  )
}
