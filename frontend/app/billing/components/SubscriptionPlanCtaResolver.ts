export type SubscriptionPlanLike = {
  id: string
  period?: string
  is_lifetime?: boolean
}

export type SubscriptionAccessLike = {
  active: boolean
  plan: string | null
}

export type PlanCtaDecision = {
  label: string
  disabled: boolean
  /**
   * Intended action:
   * - checkout: start Stripe checkout (new subscription or lifetime purchase)
   * - portal: open Stripe customer portal (change existing subscription plan)
   * - none: no action (already on this plan)
   */
  action: "checkout" | "portal" | "none"
}

export class SubscriptionPlanCtaResolver {
  private readonly hasActiveSubscription: boolean
  private readonly currentPlanCode: string | null

  constructor(subscription: SubscriptionAccessLike | null | undefined) {
    this.hasActiveSubscription = Boolean(subscription?.active)
    this.currentPlanCode = subscription?.plan ?? null
  }

  resolve(plan: SubscriptionPlanLike, purchaseBusy: boolean): PlanCtaDecision {
    const planId = plan.id
    const isLifetime = this.isLifetimePlan(plan)
    const isCurrent = this.isCurrentPlan(plan, { isLifetime })

    if (isCurrent) {
      return { label: "Current Plan", disabled: true, action: "none" }
    }

    if (this.hasActiveSubscription && !isLifetime) {
      // Avoid creating a second Stripe subscription. Use portal for recurring plan changes.
      return {
        label: "Change Plan",
        disabled: purchaseBusy,
        action: "portal",
      }
    }

    if (isLifetime) {
      return {
        label: this.hasActiveSubscription ? "Upgrade to Lifetime" : "Get Lifetime Access",
        disabled: purchaseBusy,
        action: "checkout",
      }
    }

    return { label: "Subscribe", disabled: purchaseBusy, action: "checkout" }
  }

  private isLifetimePlan(plan: SubscriptionPlanLike): boolean {
    if (plan.is_lifetime) return true
    if ((plan.period || "").toLowerCase() === "lifetime") return true
    return plan.id.toLowerCase().includes("lifetime")
  }

  private isCurrentPlan(plan: SubscriptionPlanLike, opts: { isLifetime: boolean }): boolean {
    if (!this.hasActiveSubscription) return false
    const currentCode = (this.currentPlanCode || "").trim()
    if (!currentCode) return false

    // Primary match: exact plan code match.
    const codeMatches = currentCode === plan.id

    // Defensive guard:
    // If a deployment accidentally has multiple plan rows sharing the same code, we further
    // qualify the "current plan" by matching the billing period implied by the current code.
    const currentPeriod = this.inferPeriodFromPlanCode(currentCode)
    const planPeriod = this.normalizePlanPeriod(plan, opts)
    const periodMatches = currentPeriod === planPeriod

    return codeMatches && periodMatches
  }

  private normalizePlanPeriod(plan: SubscriptionPlanLike, opts: { isLifetime: boolean }): "monthly" | "yearly" | "lifetime" {
    if (opts.isLifetime) return "lifetime"
    const p = (plan.period || "").trim().toLowerCase()
    if (p === "yearly" || p === "annual") return "yearly"
    return "monthly"
  }

  private inferPeriodFromPlanCode(planCode: string): "monthly" | "yearly" | "lifetime" {
    const code = (planCode || "").toUpperCase()
    if (code.includes("LIFETIME")) return "lifetime"
    if (code.includes("ANNUAL") || code.includes("YEAR")) return "yearly"
    return "monthly"
  }
}


