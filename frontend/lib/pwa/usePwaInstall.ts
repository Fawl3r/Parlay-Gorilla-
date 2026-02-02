'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { trackEvent } from '@/lib/track-event'

const STORAGE_KEY_DISMISSED_UNTIL = 'pg_pwa_install_dismissed_until'
const STORAGE_KEY_LAST_PROMPT_AT = 'pg_pwa_install_last_prompt_at'
const SESSION_PROMPT_COOLDOWN_MS = 30 * 60 * 1000 // 30 min same-session cooldown

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

/**
 * iOS Safari only (exclude Chrome/Firefox/Edge on iOS so "How to Install" steps stay accurate).
 */
function getIsIOS(): boolean {
  if (typeof navigator === 'undefined') return false
  const ua = navigator.userAgent
  if (!/iPhone|iPad|iPod/.test(ua)) return false
  if (/CriOS|FxiOS|EdgiOS/.test(ua)) return false // Chrome, Firefox, Edge on iOS
  return true
}

function getLastPromptAt(): number {
  if (typeof window === 'undefined') return 0
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY_LAST_PROMPT_AT)
    if (!raw) return 0
    const n = Number(raw)
    return Number.isFinite(n) ? n : 0
  } catch {
    return 0
  }
}

export interface UsePwaInstallReturn {
  isInstallable: boolean
  isInstalled: boolean
  isIOS: boolean
  shouldShowInstallCta: boolean
  dismissedUntil: number
  promptInstall: () => Promise<'accepted' | 'dismissed' | 'unavailable'>
  dismiss: (days?: number) => void
  /** Clear dismiss/cooldown so the CTA can show again (e.g. after a value moment). */
  nudgeInstallCta: () => void
}

export function usePwaInstall(): UsePwaInstallReturn {
  const [isInstallable, setIsInstallable] = useState(false)
  const [isInstalled, setIsInstalled] = useState(false)
  const [dismissedUntil, setDismissedUntil] = useState(0)
  const [lastPromptAt, setLastPromptAt] = useState(0)
  const eventRef = useRef<BeforeInstallPromptEvent | null>(null)
  const isIOS = getIsIOS()

  useEffect(() => {
    if (typeof window === 'undefined') return

    setIsInstalled(getIsInstalled())
    setDismissedUntil(getDismissedUntil())
    setLastPromptAt(getLastPromptAt())

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
      const now = Date.now()
      try {
        sessionStorage.setItem(STORAGE_KEY_LAST_PROMPT_AT, String(now))
      } catch {
        // ignore
      }
      setLastPromptAt(now)

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

  const nudgeInstallCta = useCallback(() => {
    if (typeof window === 'undefined') return
    try {
      localStorage.removeItem(STORAGE_KEY_DISMISSED_UNTIL)
      sessionStorage.removeItem(STORAGE_KEY_LAST_PROMPT_AT)
    } catch {
      // ignore
    }
    setDismissedUntil(0)
    setLastPromptAt(0)
  }, [])

  const now = typeof window !== 'undefined' ? Date.now() : 0
  const withinSessionCooldown = lastPromptAt > 0 && now - lastPromptAt < SESSION_PROMPT_COOLDOWN_MS
  const shouldShowInstallCta =
    !isInstalled &&
    (isInstallable || isIOS) &&
    now > dismissedUntil &&
    !withinSessionCooldown

  return {
    isInstallable,
    isInstalled,
    isIOS,
    shouldShowInstallCta,
    dismissedUntil,
    promptInstall,
    dismiss,
    nudgeInstallCta,
  }
}
