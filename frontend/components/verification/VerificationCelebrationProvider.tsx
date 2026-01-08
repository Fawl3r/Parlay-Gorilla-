"use client"

import React, { useCallback, useMemo, useRef, useState } from "react"

import type { VerificationSuccessModalPayload } from "@/components/verification/VerificationSuccessModal"
import { VerificationSuccessModal } from "@/components/verification/VerificationSuccessModal"
import { VerificationCelebrationRegistry } from "@/lib/verification/VerificationCelebrationRegistry"

type CelebratePayload = VerificationSuccessModalPayload

type ContextValue = {
  celebrateVerificationRecord: (payload: CelebratePayload) => void
}

const VerificationCelebrationContext = React.createContext<ContextValue | null>(null)

export function useVerificationCelebration(): ContextValue {
  const ctx = React.useContext(VerificationCelebrationContext)
  if (!ctx) {
    throw new Error("useVerificationCelebration must be used within <VerificationCelebrationProvider />")
  }
  return ctx
}

export function VerificationCelebrationProvider({ children }: { children: React.ReactNode }) {
  const registry = useMemo(() => VerificationCelebrationRegistry.fromSessionStorage(), [])
  const queueRef = useRef<CelebratePayload[]>([])
  const [active, setActive] = useState<CelebratePayload | null>(null)

  const open = Boolean(active)

  const close = useCallback(() => {
    setActive(null)
    const next = queueRef.current.shift() || null
    if (next) {
      // Let exit animation breathe before re-opening.
      setTimeout(() => setActive(next), 150)
    }
  }, [])

  const celebrateVerificationRecord = useCallback(
    (payload: CelebratePayload) => {
      const id = String(payload?.verificationRecordId || "").trim()
      if (!id) return

      if (registry.has(id)) return
      registry.mark(id)

      if (active) {
        queueRef.current.push(payload)
        return
      }
      setActive(payload)
    },
    [active, registry]
  )

  const value = useMemo<ContextValue>(
    () => ({ celebrateVerificationRecord }),
    [celebrateVerificationRecord]
  )

  return (
    <VerificationCelebrationContext.Provider value={value}>
      {children}
      <VerificationSuccessModal open={open} payload={active} onClose={close} />
    </VerificationCelebrationContext.Provider>
  )
}

export default VerificationCelebrationProvider


