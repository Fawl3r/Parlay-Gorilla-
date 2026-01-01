"use client"

import React, { useCallback, useMemo, useRef, useState } from "react"

import type { InscriptionSuccessModalPayload } from "@/components/inscriptions/InscriptionSuccessModal"
import { InscriptionSuccessModal } from "@/components/inscriptions/InscriptionSuccessModal"
import { InscriptionCelebrationRegistry } from "@/lib/inscriptions/InscriptionCelebrationRegistry"

type CelebratePayload = InscriptionSuccessModalPayload

type ContextValue = {
  celebrateInscription: (payload: CelebratePayload) => void
}

const InscriptionCelebrationContext = React.createContext<ContextValue | null>(null)

export function useInscriptionCelebration(): ContextValue {
  const ctx = React.useContext(InscriptionCelebrationContext)
  if (!ctx) {
    throw new Error("useInscriptionCelebration must be used within <InscriptionCelebrationProvider />")
  }
  return ctx
}

export function InscriptionCelebrationProvider({ children }: { children: React.ReactNode }) {
  const registry = useMemo(() => InscriptionCelebrationRegistry.fromSessionStorage(), [])
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

  const celebrateInscription = useCallback(
    (payload: CelebratePayload) => {
      const id = String(payload?.savedParlayId || "").trim()
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

  const value = useMemo<ContextValue>(() => ({ celebrateInscription }), [celebrateInscription])

  return (
    <InscriptionCelebrationContext.Provider value={value}>
      {children}
      <InscriptionSuccessModal open={open} payload={active} onClose={close} />
    </InscriptionCelebrationContext.Provider>
  )
}

export default InscriptionCelebrationProvider


