"use client"

import { Bitcoin, CreditCard, Crown, CheckCircle2 } from "lucide-react"

import type { PricingCheckoutCoordinator } from "@/app/pricing/_hooks/usePricingCheckoutCoordinator"
import type { PricingCheckoutLoadingKey } from "@/app/pricing/_hooks/usePricingCheckoutCoordinator"
import { cn } from "@/lib/utils"
import { PREMIUM_AI_PARLAYS_PER_PERIOD, PREMIUM_AI_PARLAYS_PERIOD_DAYS, PREMIUM_CUSTOM_PARLAYS_PER_DAY } from "@/lib/pricingConfig"

function isLoading(loadingKey: PricingCheckoutLoadingKey, target: string) {
  return loadingKey === target
}

type PlanModel = {
  id: "monthly" | "annual" | "lifetime"
  badge?: string
  title: string
  price: string
  subtitle: string
  features: string[]
  cardVariant: "card-monthly" | "card-annual" | "card-lifetime"
  cryptoVariant: "crypto-monthly" | "crypto-annual" | "crypto-lifetime"
  onCard: () => void
  onCrypto: () => void
}

export function PricingSubscriptionsCompact({
  checkout,
}: {
  checkout: PricingCheckoutCoordinator
}) {
  const { loadingKey } = checkout

  const plans: PlanModel[] = [
    {
      id: "monthly",
      badge: "Most popular",
      title: "Monthly",
      price: "$39.99",
      subtitle: "Renews monthly (card). Crypto is 30-day access (manual renew).",
      features: [
        `${PREMIUM_AI_PARLAYS_PER_PERIOD} AI parlays / ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days (rolling)`,
        `Custom builder (${PREMIUM_CUSTOM_PARLAYS_PER_DAY}/day)`,
        "Upset Finder + multi-sport mixing",
        "Ad-free experience",
      ],
      cardVariant: "card-monthly",
      cryptoVariant: "crypto-monthly",
      onCard: checkout.startCardMonthly,
      onCrypto: checkout.startCryptoMonthly,
    },
    {
      id: "annual",
      title: "Yearly",
      price: "$399.99",
      subtitle: "Renews yearly (card). Crypto is 365-day access (manual renew).",
      features: [
        `${PREMIUM_AI_PARLAYS_PER_PERIOD} AI parlays / ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days (rolling)`,
        `Custom builder (${PREMIUM_CUSTOM_PARLAYS_PER_DAY}/day)`,
        "Upset Finder + multi-sport mixing",
        "Ad-free experience",
      ],
      cardVariant: "card-annual",
      cryptoVariant: "crypto-annual",
      onCard: checkout.startCardAnnual,
      onCrypto: checkout.startCryptoAnnual,
    },
    {
      id: "lifetime",
      title: "Lifetime",
      price: "$500",
      subtitle: "One-time payment. Lifetime access (no renewal).",
      features: ["Everything in Premium", "No subscriptions", "Best long-term value"],
      cardVariant: "card-lifetime",
      cryptoVariant: "crypto-lifetime",
      onCard: checkout.startCardLifetime,
      onCrypto: checkout.startCryptoLifetime,
    },
  ]

  return (
    <section id="subscriptions" className="scroll-mt-28" data-testid="pricing-subscriptions">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl md:text-3xl font-black text-white">Subscriptions</h2>
          <p className="mt-1 text-sm text-gray-200/70">Upgrade for premium tools and higher limits.</p>
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {plans.map((p) => {
          const busy = loadingKey !== null
          const loadingCard = isLoading(loadingKey, p.cardVariant)
          const loadingCrypto = isLoading(loadingKey, p.cryptoVariant)

          return (
            <div
              key={p.id}
              className="relative rounded-3xl border border-white/10 bg-black/30 backdrop-blur p-6 shadow-[0_0_40px_rgba(0,0,0,0.25)]"
            >
              {p.badge ? (
                <div className="absolute -top-3 left-5 inline-flex items-center gap-2 rounded-full bg-emerald-500 px-3 py-1 text-xs font-black text-black">
                  <Crown className="h-3.5 w-3.5" />
                  {p.badge}
                </div>
              ) : null}

              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-black text-white">{p.title}</h3>
                  <div className="mt-2 text-3xl font-black text-white">{p.price}</div>
                  <p className="mt-1 text-sm text-gray-200/75">{p.subtitle}</p>
                </div>
              </div>

              <ul className="mt-5 space-y-2">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-200/80">
                    <CheckCircle2 className="h-4 w-4 text-emerald-300 mt-0.5" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>

              <div className="mt-6 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={p.onCard}
                  disabled={busy}
                  className={cn(
                    "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-bold transition-colors",
                    "bg-emerald-500 text-black hover:bg-emerald-400",
                    busy && "opacity-60"
                  )}
                  aria-label={`${p.title} (card)`}
                >
                  <CreditCard className="h-4 w-4" />
                  {loadingCard ? "Loading..." : "Card"}
                </button>
                <button
                  type="button"
                  onClick={p.onCrypto}
                  disabled={busy}
                  className={cn(
                    "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-bold transition-colors",
                    "bg-white/10 text-white hover:bg-white/20 border border-white/10",
                    busy && "opacity-60"
                  )}
                  aria-label={`${p.title} (crypto)`}
                >
                  <Bitcoin className="h-4 w-4 text-amber-300" />
                  {loadingCrypto ? "Loading..." : "Crypto"}
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}


