"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"

import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { useAuth } from "@/lib/auth-context"
import { useBeginnerMode } from "@/lib/parlay/useBeginnerMode"

import { SettingsDashboardHero, type ToggleState, type QuickToggleId } from "./components/SettingsDashboardHero"
import { SettingsCategories } from "./components/SettingsCategories"
import { AiSettingsAdvisor } from "./components/AiSettingsAdvisor"

const SAVED_DURATION_MS = 2000

function loadClientToggles(): Omit<ToggleState, "beginner"> {
  if (typeof window === "undefined") {
    return {
      aiGuidance: "standard",
      notifications: true,
      privacy: false,
    }
  }
  try {
    const raw = localStorage.getItem("pg_settings_toggles")
    if (raw) {
      const parsed = JSON.parse(raw)
      return {
        aiGuidance: parsed.aiGuidance ?? "standard",
        notifications: parsed.notifications !== false,
        privacy: Boolean(parsed.privacy),
      }
    }
  } catch {
    // ignore
  }
  return {
    aiGuidance: "standard",
    notifications: true,
    privacy: false,
  }
}

function saveClientToggles(t: Partial<ToggleState>) {
  try {
    const prev = loadClientToggles()
    const next = { ...prev, ...t }
    localStorage.setItem("pg_settings_toggles", JSON.stringify(next))
  } catch {
    // ignore
  }
}

export default function SettingsPage() {
  const router = useRouter()
  const { user, loading: authLoading, signOut } = useAuth()
  const { isBeginnerMode, setBeginnerMode } = useBeginnerMode()

  const [toggles, setToggles] = useState<ToggleState>({
    beginner: true,
    aiGuidance: "standard",
    notifications: true,
    privacy: false,
  })
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/login?redirect=/settings")
      return
    }
  }, [user, authLoading, router])

  useEffect(() => {
    setToggles((prev) => ({ ...prev, beginner: isBeginnerMode }))
  }, [isBeginnerMode])

  useEffect(() => {
    const client = loadClientToggles()
    setToggles((prev) => ({ ...prev, ...client }))
  }, [])

  const handleToggle = useCallback(
    (id: QuickToggleId, value: boolean | string) => {
      if (id === "beginner") {
        setBeginnerMode(Boolean(value))
        setToggles((p) => ({ ...p, beginner: Boolean(value) }))
      } else if (id === "aiGuidance") {
        const v = typeof value === "string" ? value : "standard"
        setToggles((p) => ({ ...p, aiGuidance: v as ToggleState["aiGuidance"] }))
        saveClientToggles({ aiGuidance: v as ToggleState["aiGuidance"] })
      } else if (id === "notifications") {
        setToggles((p) => ({ ...p, notifications: Boolean(value) }))
        saveClientToggles({ notifications: Boolean(value) })
      } else if (id === "privacy") {
        setToggles((p) => ({ ...p, privacy: Boolean(value) }))
        saveClientToggles({ privacy: Boolean(value) })
      }
      setSaved(true)
      const t = setTimeout(() => setSaved(false), SAVED_DURATION_MS)
      return () => clearTimeout(t)
    },
    [setBeginnerMode]
  )

  const handleLogout = async () => {
    await signOut()
    router.push("/auth/login")
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: "#050505" }}>
        <div className="w-8 h-8 border-2 border-[#00FF5E] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#050505" }}>
        <AnimatedBackground variant="subtle" />
        <div
          className="fixed inset-0 pointer-events-none z-[1]"
          aria-hidden
          style={{
            background:
              "linear-gradient(180deg, rgba(5,5,5,0.7) 0%, rgba(5,5,5,0.85) 50%, rgba(5,5,5,0.9) 100%)",
          }}
        />
        <main className="flex-1 py-8 px-4 relative z-10">
          <div className="max-w-6xl mx-auto">
            <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
              <h2 className="text-2xl font-black text-white">Account Control Center</h2>
              {saved && (
                <motion.span
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-sm font-semibold text-[#00FF5E]"
                >
                  Saved
                </motion.span>
              )}
            </div>

            <SettingsDashboardHero
              toggles={toggles}
              onToggle={handleToggle}
              className="mb-8"
            />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2">
                <SettingsCategories
                  email={user.email}
                  onLogout={handleLogout}
                />
              </div>
              <div>
                <AiSettingsAdvisor />
              </div>
            </div>
          </div>
        </main>
      </div>
    </DashboardLayout>
  )
}
