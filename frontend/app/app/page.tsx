import AppDashboardClient from "./AppDashboardClient"
import { Suspense } from "react"

export default function AppPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-black text-white/95 flex items-center justify-center">Loading…</div>}>
      <AppDashboardClient />
    </Suspense>
  )
}
