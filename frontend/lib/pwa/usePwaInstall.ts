'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { trackEvent } from '@/lib/track-event'

const STORAGE_KEY_DISMISSED_UNTIL = 'pg_pwa_install_dismissed_until'

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

function getDismissedUntil(): number {
  if (typeof window === 'undefined') return 0
  try {
    const raw = localStorage.getItem(STORAGE_KEY_DISMISSED_UNTIL)
    if (!raw) return 0
    const n = Number(raw)
    return Number.isFinite(n) ? n : 0
  } catch {
    return 0
  }
}

function getIsInstalled(): boolean {
  if (typeof window === 'undefined') return false
  if (window.matchMedia('(display-mode: standalone)').matches) return true
  const nav = navigator as { standalone?: boolean }
  return nav.standalone === true
}

function getIsIOS(): boolean {
  if (typeof navigator === 'undefined') return false
  return /iPhone|iPad|iPod/.test(navigator.userAgent)
}

export interface UsePwaInstallReturn {
  isInstallable: boolean
  isInstalled: boolean
  isIOS: boolean
  shouldShowInstallCta: boolean
  dismissedUntil: number
  promptInstall: () => Promise<'accepted' | 'dismissed' | 'unavailable'>
  dismiss: (days?: number) => void
}

export function usePwaInstall(): UsePwaInstallReturn {
  const [isInstallable, setIsInstallable] = useState(false)
  const [isInstalled, setIsInstalled] = useState(false)
  const [dismissedUntil, setDismissedUntil] = useState(0)
  const eventRef = useRef<BeforeInstallPromptEvent | null>(null)
  const isIOS = getIsIOS()

  useEffect(() => {
    if (typeof window === 'undefined') return

    setIsInstalled(getIsInstalled())
    setDismissedUntil(getDismissedUntil())

    const handleBeforeInstall = (e: Event) => {
      e.preventDefault()
      eventRef.current = e as BeforeInstallPromptEvent
      setIsInstallable(true)
      if (process.env.NODE_ENV === 'development') {
        console.debug('[PWA] beforeinstallprompt captured')
      }
      try {
        trackEvent('pwa_install_prompted')
      } catch {
        // optional: add when backend supports
      }
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstall)
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall)
    }
  }, [])

  const promptInstall = useCallback(async (): Promise<'accepted' | 'dismissed' | 'unavailable'> => {
    const ev = eventRef.current
    if (!ev) {
      return 'unavailable'
    }
    try {
      await ev.prompt()
      const choice = await ev.userChoice
      eventRef.current = null
      setIsInstallable(false)
      if (process.env.NODE_ENV === 'development') {
        console.debug('[PWA] userChoice:', choice.outcome)
      }
      if (choice.outcome === 'accepted') {
        try {
          trackEvent('pwa_install_accepted')
        } catch {
          // optional
        }
        return 'accepted'
      }
      try {
        trackEvent('pwa_install_dismissed')
      } catch {
        // optional
      }
      return 'dismissed'
    } catch {
      return 'unavailable'
    }
  }, [])

  const dismiss = useCallback((days = 14) => {
    if (typeof window === 'undefined') return
    const until = Date.now() + days * 24 * 60 * 60 * 1000
    try {
      localStorage.setItem(STORAGE_KEY_DISMISSED_UNTIL, String(until))
    } catch {
      // ignore
    }
    setDismissedUntil(until)
  }, [])

  const now = typeof window !== 'undefined' ? Date.now() : 0
  const shouldShowInstallCta =
    !isInstalled &&
    (isInstallable || isIOS) &&
    now > dismissedUntil

  return {
    isInstallable,
    isInstalled,
    isIOS,
    shouldShowInstallCta,
    dismissedUntil,
    promptInstall,
    dismiss,
  }
}
