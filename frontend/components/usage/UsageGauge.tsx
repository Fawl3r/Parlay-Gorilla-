"use client"

import { motion } from "framer-motion"

import { Tooltip } from "@/components/ui/tooltip"
import { UsageGaugeStatusManager, type UsageGaugeStatus } from "@/lib/usage/UsageGaugeStatusManager"
import { cn } from "@/lib/utils"

export type UsageGaugeProps = {
  label: string
  used?: number
  limit?: number | null
  valueText?: string
  helperText: string
  statusColor?: UsageGaugeStatus
  tooltip?: string
  className?: string
}

function formatLimit(limit: number | null | undefined) {
  if (limit === null || limit === undefined) return null
  if (limit < 0) return "∞"
  return String(limit)
}

export function UsageGauge({ label, used, limit, valueText, helperText, statusColor, tooltip, className }: UsageGaugeProps) {
  const statusManager = new UsageGaugeStatusManager()
  const normalizedUsed = Number.isFinite(used) ? Math.max(0, Number(used)) : 0
  const normalizedLimit = limit === null || limit === undefined ? null : Number(limit)

  const percentUsed = statusManager.getPercentUsed(normalizedUsed, normalizedLimit)
  const status = statusColor ?? statusManager.getStatus(percentUsed)
  const colors = statusManager.getColors(status)

  const size = 136
  const strokeWidth = 10
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = percentUsed === null ? circumference : circumference - (percentUsed / 100) * circumference

  const centerValue = (() => {
    if (valueText) return valueText
    const lim = formatLimit(normalizedLimit)
    if (lim === null) return String(normalizedUsed)
    return `${normalizedUsed} / ${lim} used`
  })()

  const ariaLabel = (() => {
    const lim = formatLimit(normalizedLimit)
    if (valueText) return `${label}: ${valueText}. ${helperText}`
    if (lim === null) return `${label}: ${normalizedUsed}. ${helperText}`
    return `${label}: ${normalizedUsed} of ${lim} used. ${helperText}`
  })()

  return (
    <div className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-5", className)} aria-label={ariaLabel}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs uppercase tracking-wide text-gray-200/60">{label}</div>
        </div>
        {tooltip ? <Tooltip content={tooltip} /> : null}
      </div>

      <div className="mt-4 flex items-center justify-center">
        <div className="relative" style={{ width: size, height: size }}>
          <svg width={size} height={size} aria-hidden="true">
            <circle
              className="stroke-white/10"
              fill="transparent"
              strokeWidth={strokeWidth}
              r={radius}
              cx={size / 2}
              cy={size / 2}
              strokeLinecap="round"
            />
            <motion.circle
              className={cn(colors.ring)}
              fill="transparent"
              strokeWidth={strokeWidth}
              r={radius}
              cx={size / 2}
              cy={size / 2}
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: offset }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center px-3 text-center">
            <div className={cn("text-sm font-black leading-tight", colors.glow)}>{centerValue}</div>
            {percentUsed !== null ? (
              <div className={cn("mt-1 text-xs font-semibold", colors.badge)}>{Math.round(percentUsed)}% used</div>
            ) : (
              <div className="mt-1 text-xs text-white/60">No limit</div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 text-sm text-gray-200/70">{helperText}</div>
    </div>
  )
}

export default UsageGauge


