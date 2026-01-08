"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { CreditCard, Crown, CheckCircle2 } from "lucide-react"

import type { PricingCheckoutLoadingKey } from "@/app/pricing/_hooks/usePricingCheckoutCoordinator"
import type { PricingCheckoutVariant } from "@/app/pricing/_lib/PricingCheckoutManager"
import { PREMIUM_AI_PARLAYS_PER_PERIOD, PREMIUM_AI_PARLAYS_PERIOD_DAYS, PREMIUM_CUSTOM_PARLAYS_PER_PERIOD, PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS } from "@/lib/pricingConfig"

type Props = {
  sectionId: string
  loadingKey: PricingCheckoutLoadingKey
  onUpgradeCardMonthly: () => void
  onUpgradeCardAnnual: () => void
  onUpgradeCardLifetime: () => void
}

type PlanCta = {
  variant: PricingCheckoutVariant
  label: string
  onClick: () => void
  icon: "card"
}

type PlanCardModel = {
  badge?: string
  title: string
  price: string
  subtitle: string
  features: string[]
  cta: PlanCta
}

function isLoading(loadingKey: PricingCheckoutLoadingKey, variant: PricingCheckoutVariant) {
  return loadingKey === variant
}

function PlanIcon({ icon }: { icon: PlanCta["icon"] }) {
  return <CreditCard className="h-4 w-4" />
}

function PlanCard({
  model,
  loadingKey,
}: {
  model: PlanCardModel
  loadingKey: PricingCheckoutLoadingKey
}) {
  const busy = loadingKey !== null
  const loading = isLoading(loadingKey, model.cta.variant)

  return (
    <div className="relative rounded-3xl border border-white/10 bg-black/30 backdrop-blur p-6 shadow-[0_0_40px_rgba(0,0,0,0.25)]">
      {model.badge && (
        <div className="absolute -top-3 left-5 inline-flex items-center gap-2 rounded-full bg-emerald-500 px-3 py-1 text-xs font-black text-black">
          <Crown className="h-3.5 w-3.5" />
          {model.badge}
        </div>
      )}

      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-black text-white">{model.title}</h3>
          <div className="mt-2 text-3xl font-black text-white">{model.price}</div>
          <p className="mt-1 text-sm text-gray-200/75">{model.subtitle}</p>
        </div>
      </div>

      <ul className="mt-5 space-y-2">
        {model.features.map((f) => (
          <li key={f} className="flex items-start gap-2 text-sm text-gray-200/80">
            <CheckCircle2 className="h-4 w-4 text-emerald-300 mt-0.5" />
            <span>{f}</span>
          </li>
        ))}
      </ul>

      <button
        onClick={model.cta.onClick}
        disabled={busy}
        className="mt-6 w-full inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 font-bold text-black hover:bg-emerald-400 transition-colors disabled:opacity-60"
      >
        <PlanIcon icon={model.cta.icon} />
        {loading ? "Loading..." : model.cta.label}
      </button>
    </div>
  )
}

export function PricingPlansSection({
  sectionId,
  loadingKey,
  onUpgradeCardMonthly,
  onUpgradeCardAnnual,
  onUpgradeCardLifetime,
}: Props) {
  const cards: PlanCardModel[] = [
    {
      badge: "MOST POPULAR",
      title: "Monthly (Credit Card)",
      price: "$39.99",
      subtitle: "Renews monthly. Cancel anytime and keep access until period end.",
      features: [
        `100 AI analysis generations / month`,
        `25 custom analysis scenarios / month`,
        "Automatic verification for Custom AI parlays",
        "Usage dashboard & performance insights",
      ],
      cta: { variant: "card-monthly", label: "Start monthly (Credit Card)", onClick: onUpgradeCardMonthly, icon: "card" },
    },
    {
      title: "Yearly (Credit Card)",
      price: "$399.99",
      subtitle: "Renews yearly. Cancel anytime and keep access until period end.",
      features: [
        `100 AI analysis generations / month`,
        `25 custom analysis scenarios / month`,
        "Automatic verification for Custom AI parlays",
        "Usage dashboard & performance insights",
      ],
      cta: { variant: "card-annual", label: "Start yearly (Credit Card)", onClick: onUpgradeCardAnnual, icon: "card" },
    },
    {
      title: "Lifetime (Credit Card)",
      price: "$500",
      subtitle: "One-time payment. Lifetime access (no renewal).",
      features: ["Everything in Premium", "No subscriptions", "No renewals", "Best value long-term"],
      cta: {
        variant: "card-lifetime",
        label: "Get lifetime $500 (Credit Card)",
        onClick: onUpgradeCardLifetime,
        icon: "card",
      },
    },
  ]

  return (
    <section id={sectionId} className="scroll-mt-24">
      <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-2xl md:text-3xl font-black text-white">Choose your plan</h2>
          <p className="mt-1 text-sm text-gray-200/70">
            Subscriptions auto-renew until canceled. Cancel anytime and keep access until period end.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Link
            href="/billing"
            className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-black/20 px-4 py-2 text-sm font-semibold text-white hover:bg-white/10 transition-colors"
          >
            Manage billing
          </Link>
          <Link
            href="/app"
            className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-black/20 px-4 py-2 text-sm font-semibold text-white hover:bg-white/10 transition-colors"
          >
            Continue free
          </Link>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 14 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.35 }}
        className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3"
      >
        {cards.map((c) => (
          <PlanCard key={c.title} model={c} loadingKey={loadingKey} />
        ))}
      </motion.div>

      <div className="mt-8 rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-6">
        <p className="text-sm text-gray-200/80 leading-relaxed">
          <strong className="text-white">Important:</strong> Parlay Gorilla is an analytics & research tool. We do not accept bets, process wagers, or provide gambling services. All scenarios are hypothetical and for informational/entertainment purposes only.
        </p>
      </div>
    </section>
  )
}
