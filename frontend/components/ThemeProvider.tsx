"use client"

import React from "react"

// Simplified ThemeProvider - no theme switching, just provides children
// Always uses dark theme (Parlay Gorilla theme)
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Ensure dark class is always applied
  if (typeof window !== "undefined") {
    document.documentElement.classList.add("dark")
  }

  return <>{children}</>
}

