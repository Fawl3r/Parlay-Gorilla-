"use client"

import { useEffect, useState } from "react"
import { api, SystemStatusResponse } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, Loader2 } from "lucide-react"

export function SystemStatusIndicator() {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await api.getSystemStatus()
        setStatus(data)
      } catch (error) {
        console.error("Error fetching system status:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 30000) // Refresh every 30 seconds

    return () => clearInterval(interval)
  }, [])

  if (loading || !status) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <Loader2 className="h-3 w-3 animate-spin" />
        <span>Loading status...</span>
      </div>
    )
  }

  const formatTimeAgo = (timestamp: string | null): string => {
    if (!timestamp) return "Never"
    try {
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffSec = Math.floor(diffMs / 1000)
      const diffMin = Math.floor(diffSec / 60)

      if (diffSec < 60) return `${diffSec}s ago`
      if (diffMin < 60) return `${diffMin}m ago`
      return `${Math.floor(diffMin / 60)}h ago`
    } catch {
      return "Unknown"
    }
  }

  const isOnline =
    status.scraper_last_beat_at &&
    status.settlement_last_beat_at &&
    (new Date().getTime() - new Date(status.scraper_last_beat_at).getTime()) < 300000 // 5 minutes

  return (
    <div className="flex items-center gap-3 text-xs">
      <div className="flex items-center gap-1.5">
        {isOnline ? (
          <CheckCircle2 className="h-3 w-3 text-emerald-400" />
        ) : (
          <div className="h-3 w-3 rounded-full bg-red-400" />
        )}
        <span className={isOnline ? "text-emerald-400" : "text-red-400"}>
          {isOnline ? "System Online" : "System Offline"}
        </span>
      </div>

      <div className="h-4 w-px bg-white/20" />

      <div className="text-gray-400">
        Last Sync: {formatTimeAgo(status.last_score_sync_at)}
      </div>

      <div className="h-4 w-px bg-white/20" />

      <div className="text-gray-400">
        Settled Today: <span className="text-white font-medium">{status.parlays_settled_today}</span>
      </div>
    </div>
  )
}
