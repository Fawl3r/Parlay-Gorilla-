"use client"

import { useEffect, useMemo, useState } from "react"
import { Bell, BellOff, Loader2 } from "lucide-react"
import { toast } from "sonner"

import { api } from "@/lib/api"
import { cn } from "@/lib/utils"
import { WebPushNotificationsManager } from "@/lib/notifications/WebPushNotificationsManager"

export function PushNotificationsToggle({ className }: { className?: string }) {
  const manager = useMemo(() => new WebPushNotificationsManager(api), [])
  const [loading, setLoading] = useState(true)
  const [working, setWorking] = useState(false)
  const [supported, setSupported] = useState(true)
  const [available, setAvailable] = useState(false)
  const [enabled, setEnabled] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function init() {
      try {
        if (!manager.isSupported()) {
          if (!cancelled) {
            setSupported(false)
            setAvailable(false)
            setEnabled(false)
          }
          return
        }

        const config = await manager.getServerConfig()
        if (!cancelled) setAvailable(Boolean(config.enabled && config.public_key))

        const subscribed = await manager.isSubscribed()
        if (!cancelled) setEnabled(subscribed)
      } catch {
        if (!cancelled) setAvailable(false)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    init()
    return () => {
      cancelled = true
    }
  }, [manager])

  const onToggle = async () => {
    if (working) return
    if (!supported) {
      toast.error("Notifications aren’t supported on this device/browser.")
      return
    }
    if (!available) {
      toast.error("Notifications aren’t available right now.")
      return
    }

    setWorking(true)
    try {
      if (enabled) {
        await manager.unsubscribe()
        setEnabled(false)
        toast.success("Notifications disabled")
      } else {
        await manager.subscribe()
        setEnabled(true)
        toast.success("Notifications enabled")
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Notification action failed"
      toast.error(msg)
    } finally {
      setWorking(false)
    }
  }

  const disabled = loading || working || !supported || !available
  const label = enabled ? "Alerts on" : "Alerts"

  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled}
      className={cn(
        "px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-gray-300 hover:bg-white/10 transition-all text-sm font-semibold disabled:opacity-50 inline-flex items-center gap-2",
        className
      )}
      title={!available ? "Notifications not available" : enabled ? "Disable alerts" : "Enable alerts"}
    >
      {loading || working ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : enabled ? (
        <Bell className="h-4 w-4 text-emerald-400" />
      ) : (
        <BellOff className="h-4 w-4 text-gray-400" />
      )}
      <span>{label}</span>
    </button>
  )
}


