import { cn } from "@/lib/utils"

export type AiCoachInsightProps = {
  insight: string
  className?: string
}

export function AiCoachInsight({ insight, className }: AiCoachInsightProps) {
  const safe = String(insight || "").trim()
  if (!safe) return null

  return (
    <div className={cn("rounded-2xl border border-white/10 bg-gradient-to-br from-emerald-900/15 to-black/30 backdrop-blur p-5", className)}>
      <div className="text-xs uppercase tracking-wide text-gray-200/90">AI Coach Insight</div>
      <div className="mt-2 text-sm text-white">{safe}</div>
    </div>
  )
}

export default AiCoachInsight





