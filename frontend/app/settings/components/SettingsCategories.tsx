"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import Link from "next/link"
import {
  User,
  Palette,
  Bell,
  Shield,
  Lock,
  CreditCard,
  ChevronDown,
  Mail,
  LogOut,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface CategoryConfig {
  id: string
  label: string
  icon: React.ElementType
  content: React.ReactNode
}

interface SettingsCategoriesProps {
  email?: string
  onLogout?: () => void
  className?: string
}

export function SettingsCategories({
  email,
  onLogout,
  className,
}: SettingsCategoriesProps) {
  const [expanded, setExpanded] = useState<string | null>("account")

  const categories: CategoryConfig[] = [
    {
      id: "account",
      label: "Account",
      icon: User,
      content: (
        <div className="space-y-4 pt-2">
          <div>
            <p className="text-xs uppercase text-white/50 mb-1">Email</p>
            <p className="text-white font-medium">{email ?? "—"}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              href="/profile/edit"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 text-white text-sm font-semibold hover:bg-white/15"
            >
              Edit profile
            </Link>
            {onLogout && (
              <button
                type="button"
                onClick={onLogout}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-white/10 text-white/80 text-sm font-semibold hover:bg-white/10"
              >
                <LogOut className="h-4 w-4" />
                Log out
              </button>
            )}
          </div>
        </div>
      ),
    },
    {
      id: "experience",
      label: "Experience",
      icon: Palette,
      content: (
        <div className="space-y-4 pt-2">
          <p className="text-sm text-white/70">
            Beginner mode and display preferences are in the Account Control toggles above.
          </p>
          <div className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
            <p className="text-xs uppercase text-white/50 mb-2">Animation intensity</p>
            <p className="text-white/80 text-sm">Standard (smooth micro-animations)</p>
          </div>
        </div>
      ),
    },
    {
      id: "notifications",
      label: "Notifications",
      icon: Bell,
      content: (
        <div className="space-y-4 pt-2">
          <p className="text-sm text-white/70">
            Alerts, AI recommendations, and billing notices. Toggle in Account Control.
          </p>
        </div>
      ),
    },
    {
      id: "privacy",
      label: "Privacy",
      icon: Shield,
      content: (
        <div className="space-y-4 pt-2">
          <p className="text-sm text-white/70">
            Leaderboard visibility and analytics sharing are on your{" "}
            <Link href="/profile" className="text-[#00FF5E] hover:underline">
              Profile
            </Link>
            .
          </p>
        </div>
      ),
    },
    {
      id: "security",
      label: "Security",
      icon: Lock,
      content: (
        <div className="space-y-4 pt-2">
          <p className="text-sm text-white/70">
            Sessions and connected auth. Manage in your profile and billing portal.
          </p>
        </div>
      ),
    },
    {
      id: "billing",
      label: "Billing Shortcut",
      icon: CreditCard,
      content: (
        <div className="pt-2">
          <Link
            href="/billing"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#00FF5E]/20 text-[#00FF5E] font-semibold hover:bg-[#00FF5E]/30"
          >
            <CreditCard className="h-4 w-4" />
            Open Billing Center
          </Link>
        </div>
      ),
    },
  ]

  return (
    <section className={cn("space-y-2", className)}>
      <p className="text-xs uppercase tracking-widest text-white/50 mb-4">
        Settings categories
      </p>
      <div className="grid grid-cols-1 gap-2">
        {categories.map((cat) => {
          const isOpen = expanded === cat.id
          const Icon = cat.icon
          return (
            <div
              key={cat.id}
              className="rounded-xl border border-white/10 bg-black/20 backdrop-blur overflow-hidden"
            >
              <button
                type="button"
                onClick={() => setExpanded(isOpen ? null : cat.id)}
                className="w-full flex items-center justify-between gap-4 p-4 text-left hover:bg-white/[0.03] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-5 w-5 text-[#00FF5E]" />
                  <span className="font-bold text-white">{cat.label}</span>
                </div>
                <ChevronDown
                  className={cn("h-5 w-5 text-white/50 transition-transform", isOpen && "rotate-180")}
                />
              </button>
              <AnimatePresence>
                {isOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="border-t border-white/10"
                  >
                    <div className="p-4 pt-3">{cat.content}</div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )
        })}
      </div>
    </section>
  )
}
