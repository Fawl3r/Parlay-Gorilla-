"use client"

import { Suspense, useEffect } from "react"
import { useSearchParams } from "next/navigation"

import { authSessionManager } from "@/lib/auth/session-manager"

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified"

function normalizeRedirect(raw: string | null): string {
  if (!raw) return "/app"
  const value = String(raw).trim()
  if (!value) return "/app"
  // Only allow internal paths.
  if (!value.startsWith("/")) return "/app"
  return value
}

function TestAuthClient() {
  const searchParams = useSearchParams()

  useEffect(() => {
    // Safety: prevent this utility from doing anything in production builds.
    if (process.env.NODE_ENV === "production") return

    const clear = searchParams.get("clear") === "1"
    const token = searchParams.get("token")
    const redirect = normalizeRedirect(searchParams.get("redirect"))

    try {
      localStorage.setItem(AGE_VERIFIED_KEY, "true")
    } catch {
      // ignore
    }

    if (clear) {
      authSessionManager.clearAccessToken()
      window.location.replace(redirect)
      return
    }

    if (token) {
      authSessionManager.setAccessToken(token)
    }

    window.location.replace(redirect)
  }, [searchParams])

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f] p-6">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-bold text-white mb-2">Setting session…</h1>
        <p className="text-sm text-white/60">
          Dev-only helper page. If you’re seeing this for more than a moment, refresh.
        </p>
      </div>
    </div>
  )
}

export default function TestAuthPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f] p-6">
          <div className="max-w-md text-center">
            <h1 className="text-xl font-bold text-white mb-2">Loading…</h1>
            <p className="text-sm text-white/60">Preparing session helper…</p>
          </div>
        </div>
      }
    >
      <TestAuthClient />
    </Suspense>
  )
}


