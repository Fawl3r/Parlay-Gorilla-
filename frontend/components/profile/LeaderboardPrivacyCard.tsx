"use client"

import Link from "next/link"
import { useMemo, useState } from "react"
import type { ReactNode } from "react"
import { Eye, EyeOff, Ghost, Loader2 } from "lucide-react"

import { api } from "@/lib/api"
import { cn } from "@/lib/utils"

export type LeaderboardVisibility = "public" | "anonymous" | "hidden"

function VisibilityButton({
  active,
  disabled,
  onClick,
  icon,
  title,
  subtitle,
}: {
  active: boolean
  disabled: boolean
  onClick: () => void
  icon: ReactNode
  title: string
  subtitle: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "w-full text-left rounded-xl border px-4 py-3 transition-colors",
        active ? "border-emerald-500/40 bg-emerald-500/10" : "border-white/10 bg-white/[0.03] hover:bg-white/[0.06]",
        disabled && "opacity-60 cursor-wait"
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn("mt-0.5", active ? "text-emerald-300" : "text-gray-300")}>{icon}</div>
        <div className="min-w-0">
          <div className="text-sm font-bold text-white">{title}</div>
          <div className="text-xs text-gray-200/70">{subtitle}</div>
        </div>
      </div>
    </button>
  )
}

export function LeaderboardPrivacyCard({
  initialVisibility,
  onSaved,
}: {
  initialVisibility?: LeaderboardVisibility
  onSaved?: (v: LeaderboardVisibility) => void
}) {
  const [visibility, setVisibility] = useState<LeaderboardVisibility>(initialVisibility || "public")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const options = useMemo(
    () =>
      [
        {
          id: "public" as const,
          title: "Public",
          subtitle: "Show your display name on leaderboards.",
          icon: <Eye className="h-5 w-5" />,
        },
        {
          id: "anonymous" as const,
          title: "Anonymous",
          subtitle: "Appear as a generated alias (no username).",
          icon: <Ghost className="h-5 w-5" />,
        },
        {
          id: "hidden" as const,
          title: "Hidden",
          subtitle: "Opt out completely (you won’t appear).",
          icon: <EyeOff className="h-5 w-5" />,
        },
      ] as const,
    []
  )

  const update = async (next: LeaderboardVisibility) => {
    if (saving) return
    setSaving(true)
    setError(null)
    try {
      await api.updateProfile({ leaderboard_visibility: next })
      setVisibility(next)
      onSaved?.(next)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to update privacy setting")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-white font-black">Leaderboard Privacy</h3>
          <p className="mt-1 text-sm text-gray-200/70">
            Choose how you appear on leaderboards. You can change this any time.
          </p>
        </div>
        {saving ? <Loader2 className="h-5 w-5 animate-spin text-emerald-300" /> : null}
      </div>

      <div className="mt-4 grid gap-2">
        {options.map((o) => (
          <VisibilityButton
            key={o.id}
            active={visibility === o.id}
            disabled={saving}
            onClick={() => update(o.id)}
            icon={o.icon}
            title={o.title}
            subtitle={o.subtitle}
          />
        ))}
      </div>

      {error ? <div className="mt-3 text-sm text-red-200">{error}</div> : null}

      <div className="mt-4 text-sm text-gray-200/70">
        <Link href="/leaderboards" className="text-emerald-300 hover:text-emerald-200 hover:underline">
          View leaderboards
        </Link>
      </div>
    </div>
  )
}

export default LeaderboardPrivacyCard


