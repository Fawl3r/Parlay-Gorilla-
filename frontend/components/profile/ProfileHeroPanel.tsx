"use client"

import { motion } from "framer-motion"
import {
  User,
  Mail,
  Calendar,
  Edit,
  CheckCircle,
  AlertCircle,
  Crown,
  Sparkles,
} from "lucide-react"
import type { UserProfileData } from "@/lib/api"
import { ResendVerificationEmailButton } from "./ResendVerificationEmailButton"
import { cn } from "@/lib/utils"

interface ProfileHeroPanelProps {
  user: UserProfileData
  onEdit?: () => void
  /** AI Persona derived from stats (e.g. "Strategic Builder", "Balanced Analyst") */
  personaLabel?: string
  className?: string
}

export function ProfileHeroPanel({
  user,
  onEdit,
  personaLabel,
  className,
}: ProfileHeroPanelProps) {
  const joinDate = user.created_at
    ? new Date(user.created_at).toLocaleDateString("en-US", {
        month: "long",
        year: "numeric",
      })
    : "Unknown"

  const planBadge =
    user.plan === "elite"
      ? { label: "Elite", color: "from-yellow-500 to-amber-500" }
      : user.plan === "standard"
        ? { label: "Pro", color: "from-emerald-500 to-green-500" }
        : { label: "Free", color: "from-gray-500 to-gray-600" }

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        "relative rounded-2xl border overflow-hidden",
        "bg-gradient-to-br from-white/[0.08] to-white/[0.02] backdrop-blur-xl border-white/10",
        "shadow-[0_0_40px_-12px_rgba(0,255,94,0.12)]",
        className
      )}
    >
      <div className="absolute inset-0 rounded-2xl border border-[#00FF5E]/10 pointer-events-none opacity-80" />
      <div className="relative p-6 md:p-8">
        <div className="flex flex-col md:flex-row gap-6">
          <div className="flex-shrink-0">
            <div className="relative">
              {user.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={user.display_name || "Profile"}
                  className="h-24 w-24 md:h-28 md:w-28 rounded-full object-cover border-4 border-[#00FF5E]/30"
                />
              ) : (
                <div className="h-24 w-24 md:h-28 md:w-28 rounded-full bg-gradient-to-br from-[#00FF5E]/20 to-emerald-500/10 border-4 border-[#00FF5E]/30 flex items-center justify-center">
                  <User className="h-12 w-12 md:h-14 md:w-14 text-[#00FF5E]" />
                </div>
              )}
              <div
                className={cn(
                  "absolute -bottom-2 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-bold bg-gradient-to-r text-black",
                  planBadge.color
                )}
              >
                <Crown className="inline h-3 w-3 mr-1" />
                {planBadge.label}
              </div>
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl md:text-3xl font-black text-white truncate">
                  {user.display_name || user.username || "Gorilla User"}
                </h1>
                <div className="flex items-center gap-2 mt-2">
                  <Mail className="h-4 w-4 text-white/50" />
                  <span className="text-white/70 text-sm">{user.email}</span>
                  {user.email_verified ? (
                    <span className="inline-flex items-center gap-1 text-xs text-[#00FF5E]">
                      <CheckCircle className="h-3 w-3" />
                      Verified
                    </span>
                  ) : (
                    <>
                      <span className="inline-flex items-center gap-1 text-xs text-amber-400">
                        <AlertCircle className="h-3 w-3" />
                        Unverified
                      </span>
                      <ResendVerificationEmailButton />
                    </>
                  )}
                </div>
                {!user.email_verified && (
                  <div className="mt-2 sm:hidden">
                    <ResendVerificationEmailButton />
                  </div>
                )}
                <div className="flex items-center gap-2 mt-1">
                  <Calendar className="h-4 w-4 text-white/50" />
                  <span className="text-white/60 text-sm">Member since {joinDate}</span>
                </div>
                {personaLabel && (
                  <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#00FF5E]/10 border border-[#00FF5E]/20">
                    <Sparkles className="h-4 w-4 text-[#00FF5E]" />
                    <span className="text-sm font-bold text-[#00FF5E]">AI Persona: {personaLabel}</span>
                  </div>
                )}
              </div>
              {onEdit && (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={onEdit}
                  className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white/80 hover:bg-white/10 hover:text-white transition-all"
                >
                  <Edit className="h-4 w-4" />
                  <span className="hidden sm:inline">Edit</span>
                </motion.button>
              )}
            </div>
            {user.bio && (
              <p className="mt-4 text-white/70 text-sm line-clamp-2">{user.bio}</p>
            )}
          </div>
        </div>
      </div>
    </motion.section>
  )
}

export function derivePersonaFromStats(stats: {
  by_risk_profile?: Record<string, number>
  total_parlays?: number
}): string {
  if (!stats?.by_risk_profile || !stats.total_parlays) return "Balanced Analyst"
  const degen = stats.by_risk_profile.degen ?? 0
  const conservative = stats.by_risk_profile.conservative ?? 0
  const balanced = stats.by_risk_profile.balanced ?? 0
  if (degen > conservative && degen > balanced) return "Aggressive Hunter"
  if (conservative > degen && conservative > balanced) return "Strategic Builder"
  return "Balanced Analyst"
}
