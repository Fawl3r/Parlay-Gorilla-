"use client"

import { useEffect } from "react"
import {
  trackAppOpened,
  trackOnboardingReturnSession,
  type AppOpenedSource,
} from "@/lib/track-event"

const STORAGE_LAST_SESSION_END = "pg_last_session_end"
const SESSION_KEY_APP_OPENED_FIRED = "pg_app_opened_fired"
const STORAGE_BEGINNER_MODE = "pg_beginner_mode"

function getBeginnerMode(): boolean {
  if (typeof window === "undefined") return false
  try {
    return localStorage.getItem(STORAGE_BEGINNER_MODE) === "true"
  } catch {
    return false
  }
}

function getIsPwa(): boolean {
  if (typeof window === "undefined") return false
  try {
    if (window.matchMedia("(display-mode: standalone)").matches) return true
    if ((navigator as any).standalone === true) return true
    return false
  } catch {
    return false
  }
}

function resolveSource(): AppOpenedSource {
  if (typeof window === "undefined" || typeof document === "undefined") return "direct"
  try {
    const u = new URL(window.location.href)
    const source = u.searchParams.get("source")
    if (source === "pwa" || source === "share" || source === "bookmark") return source
    if (document.referrer && document.referrer.length > 0) {
      try {
        const ref = new URL(document.referrer)
        if (ref.origin !== window.location.origin) return "direct"
      } catch {
        // ignore
      }
    }
    return "direct"
  } catch {
    return "direct"
  }
}

/**
 * Fires app_opened once per session and onboarding_return_session when user
 * returns after a previous session. Records last_session_end on pagehide for
 * next visit.
 */
export function GrowthAppOpenedTracker() {
  useEffect(() => {
    // Return session: fire if we have a previous session end time
    const lastEndRaw = typeof window !== "undefined" ? localStorage.getItem(STORAGE_LAST_SESSION_END) : null
    if (lastEndRaw) {
      const lastEnd = parseInt(lastEndRaw, 10)
      if (Number.isFinite(lastEnd)) {
        const hours = (Date.now() - lastEnd) / (1000 * 60 * 60)
        trackOnboardingReturnSession({
          hours_since_last_session: Math.round(hours * 10) / 10,
          beginner_mode: getBeginnerMode(),
        })
      }
      try {
        localStorage.removeItem(STORAGE_LAST_SESSION_END)
      } catch {
        // ignore
      }
    }

    // App opened: once per session
    try {
      if (sessionStorage.getItem(SESSION_KEY_APP_OPENED_FIRED) === "1") return
      sessionStorage.setItem(SESSION_KEY_APP_OPENED_FIRED, "1")
      trackAppOpened({
        beginner_mode: getBeginnerMode(),
        is_pwa: getIsPwa(),
        source: resolveSource(),
      })
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    function recordSessionEnd() {
      try {
        localStorage.setItem(STORAGE_LAST_SESSION_END, String(Date.now()))
      } catch {
        // ignore
      }
    }

    if (typeof window === "undefined") return
    window.addEventListener("pagehide", recordSessionEnd)
    return () => window.removeEventListener("pagehide", recordSessionEnd)
  }, [])

  return null
}
