"use client"

import { CreditCard, Crown, CheckCircle2 } from "lucide-react"

import type { PricingCheckoutCoordinator } from "@/app/pricing/_hooks/usePricingCheckoutCoordinator"
import type { PricingCheckoutLoadingKey } from "@/app/pricing/_hooks/usePricingCheckoutCoordinator"
import { cn } from "@/lib/utils"
import { PREMIUM_AI_PARLAYS_PER_PERIOD, PREMIUM_AI_PARLAYS_PERIOD_DAYS, PREMIUM_CUSTOM_PARLAYS_PER_PERIOD, PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS } from "@/lib/pricingConfig"

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
  onCard: () => void
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
      subtitle: "Renews monthly. Cancel anytime and keep access until period end.",
      features: [
        `${PREMIUM_AI_PARLAYS_PER_PERIOD} Gorilla Parlays / ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days (rolling)`,
        `Custom builder (${PREMIUM_CUSTOM_PARLAYS_PER_PERIOD}/${PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS} days)`,
        `Automatic verification for Custom AI parlays`,
        "Upset Finder + multi-sport mixing",
        "Ad-free experience",
      ],
      cardVariant: "card-monthly",
      onCard: checkout.startCardMonthly,
    },
    {
      id: "annual",
      title: "Yearly",
      price: "$399.99",
      subtitle: "Renews yearly. Cancel anytime and keep access until period end.",
      features: [
        `${PREMIUM_AI_PARLAYS_PER_PERIOD} Gorilla Parlays / ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days (rolling)`,
        `Custom builder (${PREMIUM_CUSTOM_PARLAYS_PER_PERIOD}/${PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS} days)`,
        `Automatic verification for Custom AI parlays`,
        "Upset Finder + multi-sport mixing",
        "Ad-free experience",
      ],
      cardVariant: "card-annual",
      onCard: checkout.startCardAnnual,
    },
    {
      id: "lifetime",
      badge: "LIMITED-TIME OFFER",
      title: "Lifetime",
      price: "$499.99",
      subtitle: "One-time payment. Lifetime access (no renewal).",
      features: ["Everything in Premium", "No subscriptions", "Best long-term value"],
      cardVariant: "card-lifetime",
      onCard: checkout.startCardLifetime,
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

          return (
            <div
              key={p.id}
              className="relative rounded-3xl border border-white/10 bg-black/30 backdrop-blur p-6 shadow-[0_0_40px_rgba(0,0,0,0.25)]"
            >
              {p.badge ? (
                <div className={`absolute -top-3 left-5 inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-black ${
                  p.badge === "LIMITED-TIME OFFER"
                    ? "bg-amber-500 text-black animate-pulse"
                    : "bg-emerald-500 text-black"
                }`}>
                  {p.badge !== "LIMITED-TIME OFFER" && <Crown className="h-3.5 w-3.5" />}
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

              <button
                type="button"
                onClick={p.onCard}
                disabled={busy}
                className={cn(
                  "mt-6 w-full inline-flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-bold transition-colors",
                  "bg-emerald-500 text-black hover:bg-emerald-400",
                  busy && "opacity-60"
                )}
                aria-label={`${p.title}`}
              >
                <CreditCard className="h-4 w-4" />
                {loadingCard ? "Loading..." : "Subscribe"}
              </button>
            </div>
          )
        })}
      </div>
    </section>
  )
}


