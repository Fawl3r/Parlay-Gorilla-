"use client"

import { useEffect } from "react"

/**
 * Logs build version (NEXT_PUBLIC_GIT_SHA) to console for deployment verification.
 * No visible UI. Optional: exposes value on window for production devtools when console is stripped.
 */
export function BuildVersionLogger() {
  useEffect(() => {
    const sha = process.env.NEXT_PUBLIC_GIT_SHA ?? "unknown"
    if (typeof window !== "undefined") {
      ;(window as unknown as { __PG_BUILD_SHA?: string }).__PG_BUILD_SHA = sha
      console.log("Build:", sha)
    }
  }, [])
  return null
}
