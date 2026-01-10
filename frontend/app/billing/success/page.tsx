"use client"

import { Suspense, useEffect, useMemo } from "react"
import { useSearchParams } from "next/navigation"
import { motion } from "framer-motion"
import confetti from "canvas-confetti"
import { Loader2 } from "lucide-react"

import { Header } from "@/components/Header"

import { CreditPackSuccessPanel } from "./components/CreditPackSuccessPanel"
import { ParlayPurchaseSuccessPanel } from "./components/ParlayPurchaseSuccessPanel"
import { SubscriptionSuccessPanel } from "./components/SubscriptionSuccessPanel"

type SuccessType = "sub" | "credits" | "parlay_purchase"

function parseNonNegativeInt(value: string | null): number | null {
  if (!value) return null
  const n = Number.parseInt(value, 10)
  if (!Number.isFinite(n)) return null
  if (n < 0) return null
  return n
}

function BillingSuccessContent() {
  const searchParams = useSearchParams()

  const provider = searchParams.get("provider")
  const sessionId = searchParams.get("session_id")
  const typeParam = (searchParams.get("type") || "").toLowerCase()
  const packId = searchParams.get("pack")
  const beforeBalance = parseNonNegativeInt(searchParams.get("before"))
  const expectedCredits = parseNonNegativeInt(searchParams.get("expected"))

  const successType: SuccessType = useMemo(() => {
    if (typeParam === "credits") return "credits"
    if (typeParam === "parlay_purchase") return "parlay_purchase"
    return "sub"
  }, [typeParam])

  useEffect(() => {
    const duration = 2500
    const end = Date.now() + duration

    const colors =
      successType === "credits"
        ? ["#f59e0b", "#fbbf24", "#fde68a"]
        : ["#10b981", "#34d399", "#6ee7b7"]

    const frame = () => {
      confetti({
        particleCount: 3,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors,
      })
      confetti({
        particleCount: 3,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors,
      })

      if (Date.now() < end) {
        requestAnimationFrame(frame)
      }
    }

    frame()
  }, [successType])

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
      <Header />

      <main className="flex-1 flex items-center justify-center p-4">
        <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-lg text-center">
          {successType === "credits" ? (
            <CreditPackSuccessPanel
              provider={provider}
              sessionId={sessionId}
              packId={packId}
              beforeBalance={beforeBalance}
              expectedCredits={expectedCredits}
            />
          ) : successType === "parlay_purchase" ? (
            <ParlayPurchaseSuccessPanel provider={provider} />
          ) : (
            <SubscriptionSuccessPanel provider={provider} sessionId={sessionId} />
          )}
        </motion.div>
      </main>
    </div>
  )
}

export default function BillingSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex flex-col bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
          <Header />
          <main className="flex-1 flex items-center justify-center p-4">
            <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
          </main>
        </div>
      }
    >
      <BillingSuccessContent />
    </Suspense>
  )
}


