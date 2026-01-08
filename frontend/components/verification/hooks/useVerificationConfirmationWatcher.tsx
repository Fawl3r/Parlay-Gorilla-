"use client"

import { useCallback, useEffect, useRef } from "react"

import { api } from "@/lib/api"
import type { VerificationRecordResponse, VerificationStatus } from "@/lib/api"

type Options = {
  pollIntervalMs?: number
  timeoutMs?: number
  onConfirmed?: (record: VerificationRecordResponse) => void
  onFailed?: (record: VerificationRecordResponse) => void
}

export function useVerificationConfirmationWatcher(options?: Options) {
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
      const record = await api.getVerificationRecord(id)
      const status = (record.status || "queued") as VerificationStatus
      if (status === "confirmed") {
        options?.onConfirmed?.(record)
        stop()
        return
      }
      if (status === "failed") {
        options?.onFailed?.(record)
        stop()
      }
    } catch {
      // Ignore transient polling failures.
    }
  }, [options, stop, timeoutMs])

  const watch = useCallback(
    (verificationId: string) => {
      const id = String(verificationId || "").trim()
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

  return { watchVerification: watch, stopWatching: stop }
}

export default useVerificationConfirmationWatcher


