"use client"

import { useCallback, useEffect, useState } from "react"

const STORAGE_KEY = "pg_beginner_mode"

/** Default ON for new users (no key = true). */
function readStored(): boolean {
  if (typeof window === "undefined") return true
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw === null) return true
    return raw === "true"
  } catch {
    return true
  }
}

function writeStored(value: boolean): void {
  try {
    localStorage.setItem(STORAGE_KEY, value ? "true" : "false")
  } catch {
    // ignore
  }
}

/**
 * Beginner Mode: copy layer only. When ON, we show simpler explanations
 * and suppress debug / "Why?" / technical terms (odds, markets, weeks, props).
 * Stored in localStorage; default ON for new users.
 */
export function useBeginnerMode(): {
  isBeginnerMode: boolean
  setBeginnerMode: (value: boolean) => void
} {
  const [isBeginnerMode, setState] = useState(true)

  useEffect(() => {
    setState(readStored())
  }, [])

  const setBeginnerMode = useCallback((value: boolean) => {
    setState(value)
    writeStored(value)
  }, [])

  return { isBeginnerMode, setBeginnerMode }
}

/** Read beginner mode synchronously (e.g. for SSR or initial render). */
export function getBeginnerModeStored(): boolean {
  return readStored()
}
