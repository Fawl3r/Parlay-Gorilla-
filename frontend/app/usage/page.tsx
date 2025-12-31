import { Suspense } from "react"

import UsagePerformanceClient from "./UsagePerformanceClient"

export default function UsagePerformancePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-black text-white/70 flex items-center justify-center">Loading…</div>}>
      <UsagePerformanceClient />
    </Suspense>
  )
}


