"use client"

import { useEffect } from "react"

export default function TestAgeGatePage() {
  useEffect(() => {
    // Clear the age verification
    localStorage.removeItem('parlay_gorilla_age_verified')

    // Force a full reload so the global <AgeGate /> remounts and re-reads localStorage.
    window.location.replace('/')
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f]">
      <div className="text-center text-white">
        <h1 className="text-2xl font-bold mb-4">Clearing Age Verification...</h1>
        <p className="text-muted-foreground">Redirecting to home page...</p>
      </div>
    </div>
  )
}




