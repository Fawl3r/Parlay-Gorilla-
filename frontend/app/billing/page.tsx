"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { AlertCircle, Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"

import { Footer } from "@/components/Footer"
import { Header } from "@/components/Header"
import { BillingHistory } from "@/components/profile/BillingHistory"
import { SubscriptionPanel } from "@/components/profile/SubscriptionPanel"
import { useAuth } from "@/lib/auth-context"
import { api } from "@/lib/api"
import { useSubscription } from "@/lib/subscription-context"

import { AccessIndicator } from "./components/AccessIndicator"
import { AccessStatusCards } from "./components/AccessStatusCards"
import { BillingQuickLinks } from "./components/BillingQuickLinks"
import { CreditPacksSection } from "./components/CreditPacksSection"
import { MonthlyAllowanceSection } from "./components/MonthlyAllowanceSection"
import { PaymentMethodsSection } from "./components/PaymentMethodsSection"
import { PromoCodeRedeemSection } from "./components/PromoCodeRedeemSection"
import { SubscriptionPlansSection } from "./components/SubscriptionPlansSection"
import type { AccessStatus, CheckoutProvider, CreditPack, SubscriptionPlan } from "./components/types"

export default function BillingPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()

  const [accessStatus, setAccessStatus] = useState<AccessStatus | null>(null)
  const [creditPacks, setCreditPacks] = useState<CreditPack[]>([])
  const [subscriptionPlans, setSubscriptionPlans] = useState<SubscriptionPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [purchaseLoading, setPurchaseLoading] = useState<string | null>(null)
  const [purchaseError, setPurchaseError] = useState<string | null>(null)

  const loadBillingData = useCallback(async () => {
    try {
      setLoading(true)

      const accessRes = await api.get("/api/billing/access-status")
      setAccessStatus(accessRes.data)

      const creditsRes = await api.get("/api/billing/credit-packs")
      setCreditPacks(creditsRes.data.packs || [])

      const plansRes = await api.get("/api/billing/subscription-plans")
      setSubscriptionPlans(plansRes.data.plans || [])
    } catch (err) {
      console.error("Error loading billing data:", err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/login?redirect=/billing")
      return
    }

    if (user) {
      loadBillingData()
    }
  }, [user, authLoading, router, loadBillingData])

  const sortedCreditPacks = useMemo(() => {
    return [...creditPacks].sort((a, b) => {
      // Featured packs first
      const featuredDiff = Number(Boolean(b.is_featured)) - Number(Boolean(a.is_featured))
      if (featuredDiff !== 0) return featuredDiff
      // Then sort by total credits (ascending)
      return a.total_credits - b.total_credits
    })
  }, [creditPacks])

  const { createCheckout, createPortal } = useSubscription()

  const handleBuyCreditPack = async (packId: string, provider: CheckoutProvider) => {
    try {
      setPurchaseError(null)
      setPurchaseLoading(`${packId}:${provider}`)
      const response = await api.post("/api/billing/credits/checkout", {
        credit_pack_id: packId,
        provider,
      })
      if (response.data.checkout_url) {
        const checkoutUrl = String(response.data.checkout_url)
        window.location.href = checkoutUrl
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setPurchaseError(detail || "Failed to create checkout. Please try again.")
      console.error("Error creating credit pack checkout:", err)
    } finally {
      setPurchaseLoading(null)
    }
  }

  const handleSubscribe = async (planId: string) => {
    try {
      setPurchaseError(null)
      setPurchaseLoading(planId)
      const checkoutUrl = await createCheckout("stripe", planId)
      window.location.href = checkoutUrl
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setPurchaseError(detail || "Failed to create checkout. Please try again.")
      console.error("Error creating subscription checkout:", err)
    } finally {
      setPurchaseLoading(null)
    }
  }

  const handleManagePlan = async () => {
    try {
      setPurchaseError(null)
      setPurchaseLoading("portal")
      const portalUrl = await createPortal()
      window.location.href = portalUrl
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setPurchaseError(detail || "Failed to create portal session. Please try again.")
      console.error("Error creating portal session:", err)
    } finally {
      setPurchaseLoading(null)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex flex-col bg-gradient-to-b from-[#0a0a0f] via-[#0d1117] to-[#0a0a0f]">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-[#0a0a0f] via-[#0d1117] to-[#0a0a0f]">
      <Header />

      <main className="flex-1 py-8">
        <div className="container mx-auto px-4 max-w-5xl">
          <div className="mb-8">
            <h1 className="text-2xl md:text-3xl font-black text-white mb-2">Plan &amp; Billing</h1>
            <p className="text-gray-200/70">Transparent controls for your plan, allowance, and payments — no surprises.</p>
          </div>

          {purchaseError && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 shrink-0" />
              <div className="text-sm text-red-200">{purchaseError}</div>
            </div>
          )}

          <SubscriptionPanel className="mb-8" />

          <MonthlyAllowanceSection className="mb-8" />

          <div className="mb-8">
            <BillingHistory />
          </div>

          <PaymentMethodsSection className="mb-8" />

          {accessStatus && (
            <>
              <AccessStatusCards accessStatus={accessStatus} />
              <AccessIndicator accessStatus={accessStatus} />
              <PromoCodeRedeemSection onRedeemed={loadBillingData} />
            </>
          )}

          <CreditPacksSection
            creditPacks={sortedCreditPacks}
            purchaseLoading={purchaseLoading}
            onBuy={handleBuyCreditPack}
          />

          <SubscriptionPlansSection
            subscriptionPlans={subscriptionPlans}
            accessStatus={accessStatus}
            purchaseLoading={purchaseLoading}
            onSubscribe={handleSubscribe}
          />

          <BillingQuickLinks />
        </div>
      </main>

      <Footer />
    </div>
  )
}




