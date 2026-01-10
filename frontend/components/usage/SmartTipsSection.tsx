"use client"

import { Lightbulb, Target, Zap } from "lucide-react"

import { cn } from "@/lib/utils"

type SmartTipsSectionProps = {
  className?: string
}

function TipCard({
  number,
  icon: Icon,
  title,
  description,
  className,
}: {
  number: number
  icon: React.ComponentType<{ className?: string }>
  title: string
  description: string
  className?: string
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/10 bg-gradient-to-br from-amber-900/10 to-black/30 backdrop-blur p-5 lg:p-6",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div className="rounded-lg bg-amber-500/20 p-2">
          <Icon className="w-5 h-5 text-amber-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-black text-amber-400">TIP {number}</span>
            <span className="text-sm font-black text-white">{title}</span>
          </div>
          <p className="text-sm text-gray-200/80 leading-relaxed">{description}</p>
        </div>
      </div>
    </div>
  )
}

export function SmartTipsSection({ className }: SmartTipsSectionProps) {
  return (
    <section className={cn("space-y-4", className)}>
      <div className="flex items-center gap-2">
        <Lightbulb className="w-5 h-5 text-amber-400" />
        <h2 className="text-lg font-black text-white">Smart Usage Tips</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6">
        <TipCard
          number={1}
          icon={Target}
          title="Save Custom AI"
          description="Use Custom AI Parlays for games you already like and want to target specifically. Every parlay is automatically verified on-chain."
        />

        <TipCard
          number={2}
          icon={Zap}
          title="Gorilla Parlays"
          description="Gorilla Parlays are perfect for exploring slate-wide opportunities and discovering new betting angles across multiple games."
        />

        <TipCard
          number={3}
          icon={Lightbulb}
          title="Credits Strategy"
          description="Use credits strategically when you need extra parlays. Save them for high-value opportunities."
        />
      </div>
    </section>
  )
}

