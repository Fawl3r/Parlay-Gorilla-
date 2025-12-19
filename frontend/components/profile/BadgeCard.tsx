"use client"

import { motion } from "framer-motion"
import { Lock } from "lucide-react"
import type { BadgeResponse } from "@/lib/api"

interface BadgeCardProps {
  badge: BadgeResponse
  size?: "sm" | "md" | "lg"
}

export function BadgeCard({ badge, size = "md" }: BadgeCardProps) {
  const sizeClasses = {
    sm: "p-3",
    md: "p-4",
    lg: "p-6",
  }

  const iconSizes = {
    sm: "text-2xl",
    md: "text-3xl",
    lg: "text-4xl",
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={badge.unlocked ? { scale: 1.05 } : {}}
      className={`
        relative rounded-xl border transition-all
        ${badge.unlocked 
          ? "bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/30 hover:border-emerald-500/50" 
          : "bg-white/[0.05] border-white/10 opacity-70"
        }
        ${sizeClasses[size]}
      `}
    >
      {/* Badge Icon */}
      <div className="text-center mb-2">
        <span className={`${iconSizes[size]} ${badge.unlocked ? "" : "grayscale opacity-50"}`}>
          {badge.icon || "🏆"}
        </span>
      </div>

      {/* Badge Name */}
      <h3 className={`font-semibold text-center ${badge.unlocked ? "text-white" : "text-gray-500"} ${size === "sm" ? "text-xs" : "text-sm"}`}>
        {badge.name}
      </h3>

      {/* Description (for md and lg sizes) */}
      {size !== "sm" && badge.description && (
        <p className={`text-center mt-1 ${badge.unlocked ? "text-gray-400" : "text-gray-600"} ${size === "md" ? "text-xs" : "text-sm"}`}>
          {badge.description}
        </p>
      )}

      {/* Unlock info */}
      {!badge.unlocked && (
        <div className="mt-2 text-center">
          <div className="inline-flex items-center gap-1 text-xs text-gray-500">
            <Lock className="h-3 w-3" />
            <span>{badge.requirement_value} {badge.requirement_type === "TOTAL_PARLAYS" ? "parlays" : "required"}</span>
          </div>
        </div>
      )}

      {/* Unlocked date */}
      {badge.unlocked && badge.unlocked_at && (
        <p className="text-xs text-emerald-400/70 text-center mt-2">
          {new Date(badge.unlocked_at).toLocaleDateString()}
        </p>
      )}

      {/* Glow effect for unlocked badges */}
      {badge.unlocked && (
        <div className="absolute inset-0 rounded-xl bg-emerald-500/5 blur-xl -z-10" />
      )}
    </motion.div>
  )
}

