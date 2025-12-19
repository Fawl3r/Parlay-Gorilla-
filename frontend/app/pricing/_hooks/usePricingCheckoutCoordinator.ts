"use client"

import { useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"
import { PricingCheckoutManager, PricingCheckoutVariant } from "@/app/pricing/_lib/PricingCheckoutManager"

export type PricingCheckoutLoadingKey = PricingCheckoutVariant | null

/**
 * UI + navigation coordinator for Pricing checkout actions.
 *
 * - Manages loading states for CTA buttons
 * - Enforces auth by sending users to login (and returning them to /pricing)
 * - Delegates checkout business logic to `PricingCheckoutManager`
 */
export function usePricingCheckoutCoordinator() {
  const router = useRouter()
  const { user } = useAuth()
  const { createCheckout } = useSubscription()

  const [loadingKey, setLoadingKey] = useState<PricingCheckoutLoadingKey>(null)

  const manager = useMemo(() => new PricingCheckoutManager(createCheckout), [createCheckout])

  const start = async (variant: PricingCheckoutVariant) => {
    setLoadingKey(variant)

    try {
      const action = await manager.beginCheckout({
        variant,
        isAuthenticated: Boolean(user),
        redirectAfterLogin: "/pricing",
      })

      if (action.kind === "auth_required") {
        sessionStorage.setItem("redirectAfterLogin", action.redirectAfterLogin)
        router.push("/auth/login")
        return
      }

      if (action.kind === "redirect") {
        window.location.href = action.url
        return
      }

      toast.error(action.message)
    } catch (error) {
      console.error("[Pricing] Checkout error:", error)
      toast.error("Checkout failed. Please try again.")
    } finally {
      setLoadingKey(null)
    }
  }

  return {
    loadingKey,
    startCardMonthly: () => start("card-monthly"),
    startCardAnnual: () => start("card-annual"),
    startCardLifetime: () => start("card-lifetime"),
    startCryptoMonthly: () => start("crypto-monthly"),
    startCryptoAnnual: () => start("crypto-annual"),
    startCryptoLifetime: () => start("crypto-lifetime"),
  }
}

export type PricingCheckoutCoordinator = ReturnType<typeof usePricingCheckoutCoordinator>


