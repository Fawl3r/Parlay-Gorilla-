import { cn } from "@/lib/utils"

export type MiniUsageBarProps = {
  remaining: number
  limit: number
  segments?: number
  className?: string
}

function normalizeInt(x: number) {
  return Number.isFinite(x) ? Math.max(0, Math.floor(x)) : 0
}

export function MiniUsageBar({ remaining, limit, segments = 10, className }: MiniUsageBarProps) {
  const lim = normalizeInt(limit)
  const rem = normalizeInt(remaining)
  const segs = Math.max(5, Math.min(20, normalizeInt(segments)))

  if (lim <= 0) return null

  const ratio = Math.max(0, Math.min(1, rem / lim))
  const filled = Math.round(ratio * segs)

  return (
    <div className={cn("inline-flex items-center gap-2", className)} aria-label={`${rem} of ${lim} remaining`}>
      <div className="flex items-center gap-0.5">
        {Array.from({ length: segs }).map((_, idx) => (
          <span
            key={idx}
            className={cn(
              "h-2 w-1.5 rounded-sm",
              idx < filled ? "bg-emerald-400/80" : "bg-white/15"
            )}
          />
        ))}
      </div>
      <span className="text-xs text-white/95">{rem} left</span>
    </div>
  )
}

export default MiniUsageBar





