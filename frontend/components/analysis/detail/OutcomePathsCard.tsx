"use client"

import { cn } from "@/lib/utils"
import type { OutcomePaths } from "@/lib/api/types/analysis"
import { TrendingUp, Target, Zap } from "lucide-react"

export type OutcomePathsCardProps = {
  outcomePaths?: OutcomePaths
  className?: string
}

export function OutcomePathsCard({ outcomePaths, className }: OutcomePathsCardProps) {
  if (!outcomePaths) return null

  const paths = [
    {
      key: "home_control_script",
      label: "Home Control",
      icon: Target,
      color: "bg-blue-500",
      data: outcomePaths.home_control_script,
    },
    {
      key: "shootout_script",
      label: "Shootout",
      icon: Zap,
      color: "bg-orange-500",
      data: outcomePaths.shootout_script,
    },
    {
      key: "variance_upset_script",
      label: "Variance Upset",
      icon: TrendingUp,
      color: "bg-purple-500",
      data: outcomePaths.variance_upset_script,
    },
  ]

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur-sm p-5", className)}>
      <div className="text-sm font-extrabold text-white mb-4">Outcome Paths</div>
      {outcomePaths.explanation && (
        <p className="text-xs text-white/60 mb-4">{outcomePaths.explanation}</p>
      )}
      <div className="space-y-4">
        {paths.map((path) => {
          const Icon = path.icon
          const prob = Math.round((path.data.probability || 0) * 100)
          return (
            <div key={path.key} className="rounded-lg border border-white/5 bg-white/5 p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4 text-white/60" />
                  <span className="text-sm font-semibold text-white">{path.label}</span>
                </div>
                <span className="text-sm font-bold text-white">{prob}%</span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-white/10 overflow-hidden">
                <div
                  className={cn("h-full transition-all duration-500", path.color)}
                  style={{ width: `${prob}%` }}
                />
              </div>
              <p className="text-xs text-white/60 mt-2">{path.data.description}</p>
              {path.data.recommended_angles && path.data.recommended_angles.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {path.data.recommended_angles.map((angle, idx) => (
                    <span
                      key={idx}
                      className="text-xs px-2 py-0.5 rounded bg-white/10 text-white/70"
                    >
                      {angle}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}
