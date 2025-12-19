"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { 
  User, 
  Mail, 
  Calendar, 
  Edit, 
  CheckCircle, 
  AlertCircle,
  Crown
} from "lucide-react"
import type { UserProfileData } from "@/lib/api"
import { GlassPanel } from "@/components/ui/glass-panel"
import { ResendVerificationEmailButton } from "@/components/profile/ResendVerificationEmailButton"

interface ProfileHeaderProps {
  user: UserProfileData
  onEdit?: () => void
}

export function ProfileHeader({ user, onEdit }: ProfileHeaderProps) {
  const joinDate = user.created_at 
    ? new Date(user.created_at).toLocaleDateString("en-US", { 
        month: "long", 
        year: "numeric" 
      })
    : "Unknown"

  const getPlanBadge = () => {
    switch (user.plan) {
      case "elite":
        return { label: "Elite", color: "from-yellow-500 to-amber-500" }
      case "standard":
        return { label: "Pro", color: "from-emerald-500 to-green-500" }
      default:
        return { label: "Free", color: "from-gray-500 to-gray-600" }
    }
  }

  const planBadge = getPlanBadge()

  return (
    <GlassPanel
      tone="strong"
      padding="none"
      className="rounded-2xl p-6 md:p-8 bg-gradient-to-br from-white/[0.08] to-white/[0.03]"
    >
      <div className="flex flex-col md:flex-row gap-6">
        {/* Avatar Section */}
        <div className="flex-shrink-0">
          <div className="relative">
            {user.avatar_url ? (
              <img
                src={user.avatar_url}
                alt={user.display_name || "Profile"}
                className="h-24 w-24 md:h-32 md:w-32 rounded-full object-cover border-4 border-emerald-500/30"
              />
            ) : (
              <div className="h-24 w-24 md:h-32 md:w-32 rounded-full bg-gradient-to-br from-emerald-500/20 to-green-500/10 border-4 border-emerald-500/30 flex items-center justify-center">
                <User className="h-12 w-12 md:h-16 md:w-16 text-emerald-400" />
              </div>
            )}
            
            {/* Plan Badge */}
            <div className={`absolute -bottom-2 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-bold bg-gradient-to-r ${planBadge.color} text-black`}>
              <Crown className="inline h-3 w-3 mr-1" />
              {planBadge.label}
            </div>
          </div>
        </div>

        {/* Info Section */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-white truncate">
                {user.display_name || user.username || "Gorilla User"}
              </h1>
              
              {/* Email with verification status */}
              <div className="flex items-center gap-2 mt-2">
                <Mail className="h-4 w-4 text-gray-500" />
                <span className="text-gray-400 text-sm">{user.email}</span>
                {user.email_verified ? (
                  <span className="inline-flex items-center gap-1 text-xs text-emerald-400">
                    <CheckCircle className="h-3 w-3" />
                    Verified
                  </span>
                ) : (
                  <>
                    <span className="inline-flex items-center gap-1 text-xs text-yellow-400">
                      <AlertCircle className="h-3 w-3" />
                      Unverified
                    </span>
                    <span className="hidden sm:inline">
                      <ResendVerificationEmailButton />
                    </span>
                  </>
                )}
              </div>

              {/* Mobile: show resend button on its own line */}
              {!user.email_verified && (
                <div className="mt-3 sm:hidden">
                  <ResendVerificationEmailButton />
                </div>
              )}

              {/* Join Date */}
              <div className="flex items-center gap-2 mt-1">
                <Calendar className="h-4 w-4 text-gray-500" />
                <span className="text-gray-400 text-sm">Joined {joinDate}</span>
              </div>
            </div>

            {/* Edit Button */}
            {onEdit && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onEdit}
                className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-300 hover:bg-white/10 hover:text-white transition-all"
              >
                <Edit className="h-4 w-4" />
                <span className="hidden sm:inline">Edit</span>
              </motion.button>
            )}
          </div>

          {/* Bio */}
          {user.bio && (
            <p className="mt-4 text-gray-300 text-sm line-clamp-2">{user.bio}</p>
          )}

          {/* Tags */}
          <div className="flex flex-wrap gap-2 mt-4">
            {/* Risk Profile */}
            <span className="px-3 py-1 bg-white/5 rounded-full text-xs text-gray-400">
              {user.default_risk_profile === "degen" ? "🔥" : user.default_risk_profile === "conservative" ? "🛡️" : "⚖️"} 
              {" "}{user.default_risk_profile.charAt(0).toUpperCase() + user.default_risk_profile.slice(1)}
            </span>

            {/* Favorite Sports */}
            {user.favorite_sports?.slice(0, 3).map((sport) => (
              <span key={sport} className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-xs text-emerald-400">
                {sport}
              </span>
            ))}
            
            {user.favorite_sports?.length > 3 && (
              <span className="px-3 py-1 bg-white/5 rounded-full text-xs text-gray-500">
                +{user.favorite_sports.length - 3} more
              </span>
            )}
          </div>
        </div>
      </div>
    </GlassPanel>
  )
}

