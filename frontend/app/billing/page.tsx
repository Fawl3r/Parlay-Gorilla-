"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { AlertCircle, Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"

import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { BillingHistory } from "@/components/profile/BillingHistory"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { useAuth } from "@/lib/auth-context"
import { api } from "@/lib/api"
import { StripeReconcileService } from "@/lib/billing/StripeReconcileService"
import { useSubscription } from "@/lib/subscription-context"
import { formatPlanName } from "@/lib/utils/planNameFormatter"

import { AccessIndicator } from "./components/AccessIndicator"
import { BillingStatusHero } from "./components/BillingStatusHero"
import { UsageVisualization } from "./components/UsageVisualization"
import { CreditEconomicsPanel } from "./components/CreditEconomicsPanel"
import { PlanComparisonSmart } from "./components/PlanComparisonSmart"
import { BillingActionCenter } from "./components/BillingActionCenter"
import { PromoCodeRedeemSection } from "./components/PromoCodeRedeemSection"
import type { AccessStatus, CheckoutProvider, CreditPack, SubscriptionPlan } from "./components/types"

export default function BillingPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()

  const [accessStatus, setAccessStatus] = useState<AccessStatus | null>(null)
  const [creditPacks, setCreditPacks] = useState<CreditPack[]>([])
  const [subscriptionPlans, setSubscriptionPlans] = useState<SubscriptionPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [purchaseLoading, setPurchaseLoading] = useState<string | null>(null)
  const [syncLoading, setSyncLoading] = useState(false)
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
    if (user) loadBillingData()
  }, [user, authLoading, router, loadBillingData])

  const sortedCreditPacks = useMemo(() => {
    return [...creditPacks].sort((a, b) => {
      const featuredDiff = Number(Boolean(b.is_featured)) - Number(Boolean(a.is_featured))
      if (featuredDiff !== 0) return featuredDiff
      return a.total_credits - b.total_credits
    })
  }, [creditPacks])

  const { createCheckout, createPortal } = useSubscription()

  const handleBuyCreditPack = async (packId: string, provider: CheckoutProvider) => {
    if (!user?.email_verified) {
      setPurchaseError("Please verify your email address before making a purchase. Check your inbox for the verification link.")
      return
    }
    try {
      setPurchaseError(null)
      setPurchaseLoading(`${packId}:${provider}`)
      const response = await api.post("/api/billing/credits/checkout", {
        credit_pack_id: packId,
        provider,
      })
      if (response.data.checkout_url) {
        window.location.href = String(response.data.checkout_url)
      }
    } catch (err: any) {
      setPurchaseError(err?.response?.data?.detail || "Failed to create checkout. Please try again.")
      console.error("Error creating credit pack checkout:", err)
    } finally {
      setPurchaseLoading(null)
    }
  }

  const handleSubscribe = async (planId: string) => {
    if (!user?.email_verified) {
      setPurchaseError("Please verify your email address before making a purchase. Check your inbox for the verification link.")
      return
    }
    try {
      setPurchaseError(null)
      setPurchaseLoading(planId)
      const checkoutUrl = await createCheckout(planId)
      window.location.href = checkoutUrl
    } catch (err: any) {
      setPurchaseError(err?.response?.data?.detail || "Failed to create checkout. Please try again.")
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
      setPurchaseError(err?.response?.data?.detail || "Failed to create portal session. Please try again.")
      console.error("Error creating portal session:", err)
    } finally {
      setPurchaseLoading(null)
    }
  }

  const handleSyncBilling = async () => {
    try {
      setPurchaseError(null)
      setSyncLoading(true)
      const reconciler = new StripeReconcileService()
      await reconciler.reconcileLatest()
      await loadBillingData()
    } catch (err: any) {
      setPurchaseError(err?.response?.data?.detail || "Failed to sync billing. Please try again.")
      console.error("Error syncing billing:", err)
    } finally {
      setSyncLoading(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex flex-col" style={{ backgroundColor: "#0b0b0b" }}>
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
        </main>
        <Footer />
      </div>
    )
  }

  const planName = accessStatus?.subscription?.plan
    ? formatPlanName(accessStatus.subscription.plan)
    : "Free"
  const isLifetime = accessStatus?.subscription?.is_lifetime ?? false

  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0b0b0b" }}>
        <AnimatedBackground variant="subtle" />
        <div
          className="fixed inset-0 pointer-events-none z-[1]"
          aria-hidden
          style={{
            background:
              "linear-gradient(180deg, rgba(14,14,14,0.55) 0%, rgba(14,14,14,0.7) 50%, rgba(14,14,14,0.78) 100%)",
          }}
        />
        <main className="flex-1 py-8 relative z-10">
          <div className="container mx-auto px-4 max-w-5xl">
            {purchaseError && (
              <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 shrink-0" />
                <div className="text-sm text-red-200">{purchaseError}</div>
              </div>
            )}

            <BillingStatusHero
              accessStatus={accessStatus}
              planName={planName}
              isLifetime={isLifetime}
              className="mb-8"
            />

            <UsageVisualization accessStatus={accessStatus} className="mb-8" />

            <CreditEconomicsPanel
              creditPacks={sortedCreditPacks}
              purchaseLoading={purchaseLoading}
              onBuy={handleBuyCreditPack}
              isEmailVerified={user?.email_verified ?? false}
              className="mb-8"
            />

            <PlanComparisonSmart
              subscriptionPlans={subscriptionPlans}
              accessStatus={accessStatus}
              purchaseLoading={purchaseLoading}
              onSubscribe={handleSubscribe}
              onManagePlan={handleManagePlan}
              isEmailVerified={user?.email_verified ?? false}
              className="mb-8"
            />

            <BillingActionCenter
              onManagePayment={handleManagePlan}
              onSyncBilling={handleSyncBilling}
              loadingPortal={purchaseLoading === "portal"}
              loadingSync={syncLoading}
              className="mb-8"
            />

            <div className="mb-8">
              <BillingHistory />
            </div>

            {accessStatus && (
              <>
                <AccessIndicator accessStatus={accessStatus} />
                <PromoCodeRedeemSection onRedeemed={loadBillingData} />
              </>
            )}
          </div>
        </main>
      </div>
    </DashboardLayout>
  )
}
