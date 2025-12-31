"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { Coins, CreditCard, Loader2 } from "lucide-react"

import { api } from "@/lib/api"
import { useAuth } from "@/lib/auth-context"
import { LemonSqueezyAffiliateUrlBuilder } from "@/lib/lemonsqueezy/LemonSqueezyAffiliateUrlBuilder"
import { cn } from "@/lib/utils"

type CreditPack = {
  id: string
  name: string
  price: number
  credits: number
  bonus_credits: number
  total_credits: number
  price_per_credit: number
  is_featured?: boolean
}

type Provider = "lemonsqueezy" | "coinbase"

export function CreditPacksSection() {
  const router = useRouter()
  const { user } = useAuth()

  const [packs, setPacks] = useState<CreditPack[]>([])
  const [loading, setLoading] = useState(true)
  const [busyKey, setBusyKey] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        setLoading(true)
        setError(null)
        const res = await api.get("/api/billing/credit-packs")
        if (cancelled) return
        setPacks((res.data?.packs || []) as CreditPack[])
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "Failed to load credit packs")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  const sorted = useMemo(() => {
    return [...packs].sort((a, b) => {
      // Featured packs first
      const featuredDiff = Number(Boolean(b.is_featured)) - Number(Boolean(a.is_featured))
      if (featuredDiff !== 0) return featuredDiff
      // Then sort by total credits (ascending)
      return a.total_credits - b.total_credits
    })
  }, [packs])

  const startCheckout = async (packId: string, provider: Provider) => {
    if (!user) {
      sessionStorage.setItem("redirectAfterLogin", "/pricing#credits")
      router.push("/auth/login")
      return
    }

    const key = `${packId}:${provider}`
    setBusyKey(key)
    setError(null)

    try {
      const res = await api.post("/api/billing/credits/checkout", {
        credit_pack_id: packId,
        provider,
      })
      const checkoutUrl = String(res.data?.checkout_url || "")
      if (!checkoutUrl) throw new Error("Checkout failed")

      const finalUrl =
        provider === "lemonsqueezy"
          ? await new LemonSqueezyAffiliateUrlBuilder().build(checkoutUrl)
          : checkoutUrl

      window.location.href = finalUrl
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      setError(detail || e?.message || "Failed to create checkout")
    } finally {
      setBusyKey(null)
    }
  }

  return (
    <section id="credits" className="scroll-mt-28">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl md:text-3xl font-black text-white">Credit packs</h2>
          <p className="mt-1 text-sm text-gray-200/70">Pay per use. No subscription required.</p>
        </div>
      </div>

      {error ? (
        <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      ) : null}

      {loading ? (
        <div className="mt-6 flex items-center gap-2 text-gray-300">
          <Loader2 className="h-5 w-5 animate-spin text-emerald-400" />
          Loading credit packs...
        </div>
      ) : (
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {sorted.map((pack) => (
            <div
              key={pack.id}
              className={cn(
                "rounded-2xl border bg-black/25 backdrop-blur p-4",
                pack.is_featured ? "border-amber-500/30" : "border-white/10"
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-bold text-white">{pack.name}</div>
                  <div className="mt-1 text-xs text-gray-400">${pack.price.toFixed(2)} • ${pack.price_per_credit.toFixed(2)}/credit</div>
                </div>
                <div className="inline-flex items-center gap-1 rounded-full bg-white/5 border border-white/10 px-2 py-1 text-[10px] text-gray-300">
                  <Coins className="h-3 w-3 text-amber-400" />
                  {pack.total_credits}
                </div>
              </div>

              {pack.bonus_credits > 0 ? (
                <div className="mt-2 text-xs text-emerald-300">+{pack.bonus_credits} bonus credits</div>
              ) : (
                <div className="mt-2 text-xs text-gray-500">No bonus credits</div>
              )}

              <div className="mt-4 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => startCheckout(pack.id, "lemonsqueezy")}
                  disabled={busyKey !== null}
                  className={cn(
                    "inline-flex items-center justify-center gap-2 rounded-xl px-3 py-2 text-xs font-bold transition-colors",
                    "bg-amber-500 text-black hover:bg-amber-400",
                    busyKey !== null && "opacity-60"
                  )}
                >
                  {busyKey === `${pack.id}:lemonsqueezy` ? <Loader2 className="h-4 w-4 animate-spin" /> : <CreditCard className="h-4 w-4" />}
                  Card
                </button>
                <button
                  type="button"
                  onClick={() => startCheckout(pack.id, "coinbase")}
                  disabled={busyKey !== null}
                  className={cn(
                    "inline-flex items-center justify-center gap-2 rounded-xl px-3 py-2 text-xs font-bold transition-colors",
                    "bg-white/10 text-white hover:bg-white/20 border border-white/10",
                    busyKey !== null && "opacity-60"
                  )}
                >
                  {busyKey === `${pack.id}:coinbase` ? <Loader2 className="h-4 w-4 animate-spin" /> : <Coins className="h-4 w-4 text-amber-400" />}
                  Crypto
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}


