/**
 * Premium gating helpers for conversion/upgrade surfaces.
 * Ensures upgrade prompts and blurred overlays never show to premium users
 * and avoid flicker until auth/subscription is resolved.
 */

export interface UserState {
  isPremium: boolean
  loading: boolean
}

/** True when user has an active premium subscription. */
export function isPremiumUser(isPremium: boolean): boolean {
  return isPremium === true
}

/** True when subscription/auth state has been resolved (no longer loading). */
export function isAuthResolved(loading: boolean): boolean {
  return loading === false
}

/** Safe to show upgrade surface only when not premium and auth is resolved. */
export function shouldShowUpgradeSurface(state: UserState): boolean {
  return !isPremiumUser(state.isPremium) && isAuthResolved(state.loading)
}
