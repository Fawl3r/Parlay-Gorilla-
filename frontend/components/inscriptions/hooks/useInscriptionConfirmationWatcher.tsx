"use client"

import { useCallback, useEffect, useRef } from "react"

import { api } from "@/lib/api"
import type { InscriptionStatus, SavedParlayResponse } from "@/lib/api"

type Options = {
  pollIntervalMs?: number
  timeoutMs?: number
  onConfirmed?: (item: SavedParlayResponse) => void
  onFailed?: (item: SavedParlayResponse) => void
}

async function fetchSavedParlayById(id: string): Promise<SavedParlayResponse | null> {
  const list = await api.listSavedParlays("custom", 100, false)
  return list.find((p) => p.id === id) || null
}

export function useInscriptionConfirmationWatcher(options?: Options) {
  const pollIntervalMs = Math.max(1000, options?.pollIntervalMs ?? 4000)
  const timeoutMs = Math.max(5000, options?.timeoutMs ?? 60_000)

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const watchingIdRef = useRef<string | null>(null)
  const startedAtRef = useRef<number>(0)

  const stop = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current)
    intervalRef.current = null
    watchingIdRef.current = null
    startedAtRef.current = 0
  }, [])

  const tick = useCallback(async () => {
    const id = watchingIdRef.current
    if (!id) return

    const elapsed = Date.now() - startedAtRef.current
    if (elapsed > timeoutMs) {
      stop()
      return
    }

    try {
      const item = await fetchSavedParlayById(id)
      if (!item) return

      const status = (item.inscription_status || "none") as InscriptionStatus
      if (status === "confirmed") {
        options?.onConfirmed?.(item)
        stop()
        return
      }
      if (status === "failed") {
        options?.onFailed?.(item)
        stop()
      }
    } catch {
      // Ignore transient polling failures.
    }
  }, [options, stop, timeoutMs])

  const watch = useCallback(
    (savedParlayId: string) => {
      const id = String(savedParlayId || "").trim()
      if (!id) return

      stop()
      watchingIdRef.current = id
      startedAtRef.current = Date.now()
      intervalRef.current = setInterval(() => {
        void tick()
      }, pollIntervalMs)
      void tick()
    },
    [pollIntervalMs, stop, tick]
  )

  useEffect(() => stop, [stop])

  return { watchInscription: watch, stopWatching: stop }
}

export default useInscriptionConfirmationWatcher


