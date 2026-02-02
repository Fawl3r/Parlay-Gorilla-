'use client'

import { useEffect, useRef } from 'react'
import { toast } from 'sonner'
import { usePwaInstallContext } from '@/lib/pwa/PwaInstallContext'
import { useSubscription } from '@/lib/subscription-context'

const INSTALLED_TOAST_STORAGE_KEY = 'pg_pwa_installed_toast_shown'
const INSTALLED_TOAST_MESSAGE = 'Installed ✅ Launch Parlay Gorilla from your home screen anytime.'

/**
 * When PWA is installed: sets data-app-mode="pwa" on <html> and shows a one-time toast.
 * When user becomes premium: nudges the PWA install CTA so it can re-appear.
 */
export function PwaAppModeAndToast() {
  const { isInstalled, nudgeInstallCta } = usePwaInstallContext()
  const { isPremium } = useSubscription()
  const prevPremiumRef = useRef<boolean | null>(null)

  // App mode attribute for PWA-only styling (safe area, spacing)
  useEffect(() => {
    if (typeof document === 'undefined') return
    const el = document.documentElement
    if (isInstalled) {
      el.setAttribute('data-app-mode', 'pwa')
    } else {
      el.removeAttribute('data-app-mode')
    }
    return () => el.removeAttribute('data-app-mode')
  }, [isInstalled])

  // One-time "installed" toast
  useEffect(() => {
    if (!isInstalled || typeof window === 'undefined') return
    try {
      if (localStorage.getItem(INSTALLED_TOAST_STORAGE_KEY) === '1') return
      toast.success(INSTALLED_TOAST_MESSAGE)
      localStorage.setItem(INSTALLED_TOAST_STORAGE_KEY, '1')
    } catch {
      // ignore
    }
  }, [isInstalled])

  // Nudge install CTA when user becomes premium
  useEffect(() => {
    if (prevPremiumRef.current === null) {
      prevPremiumRef.current = isPremium
      return
    }
    if (!prevPremiumRef.current && isPremium) {
      nudgeInstallCta()
    }
    prevPremiumRef.current = isPremium
  }, [isPremium, nudgeInstallCta])

  return null
}
