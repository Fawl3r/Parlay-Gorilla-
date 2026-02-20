"use client"

import { motion } from "framer-motion"
import { Trophy, Flame, Lock, Check } from "lucide-react"
import { cn } from "@/lib/utils"

interface ProgressionSystemProps {
  totalParlays: number
  /** Next milestone (e.g. 10, 25, 50) — client-only, not persisted */
  nextMilestone?: number
  /** Streak days — client-only, derived or placeholder */
  streakDays?: number
  className?: string
}

const MILESTONES = [5, 10, 25, 50, 100, 250]

export function ProgressionSystem({
  totalParlays,
  nextMilestone = 10,
  streakDays = 0,
  className,
}: ProgressionSystemProps) {
  const achieved = MILESTONES.filter((m) => totalParlays >= m)
  const next = MILESTONES.find((m) => m > totalParlays) ?? MILESTONES[MILESTONES.length - 1]
  const progressToNext = next > 0 ? Math.min(100, (totalParlays / next) * 100) : 100

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.25 }}
      className={cn(
        "rounded-2xl border border-white/10 bg-black/20 backdrop-blur p-6",
        className
      )}
    >
      <p className="text-xs uppercase tracking-widest text-white/50 mb-4">
        Progression
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div>
          <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
            <Trophy className="h-4 w-4 text-amber-400" />
            Activity milestones
          </h3>
          <div className="flex flex-wrap gap-2 mb-3">
            {MILESTONES.map((m) => {
              const unlocked = totalParlays >= m
              return (
                <div
                  key={m}
                  className={cn(
                    "flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold",
                    unlocked
                      ? "bg-[#00FF5E]/20 text-[#00FF5E]"
                      : "bg-white/5 text-white/50"
                  )}
                >
                  {unlocked ? <Check className="h-3 w-3" /> : <Lock className="h-3 w-3" />}
                  {m}
                </div>
              )
            })}
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-white/60">Progress to {next} parlays</span>
              <span className="text-white/90 font-semibold">{progressToNext.toFixed(0)}%</span>
            </div>
            <div className="h-2 rounded-full bg-white/10 overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progressToNext}%` }}
                transition={{ duration: 0.6 }}
                className="h-full bg-gradient-to-r from-[#00FF5E] to-emerald-400 rounded-full"
              />
            </div>
          </div>
        </div>
        <div>
          <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
            <Flame className="h-4 w-4 text-orange-400" />
            Usage streak
          </h3>
          <p className="text-2xl font-black text-white">{streakDays}</p>
          <p className="text-xs text-white/50">days active (indicator)</p>
        </div>
      </div>
    </motion.section>
  )
}
