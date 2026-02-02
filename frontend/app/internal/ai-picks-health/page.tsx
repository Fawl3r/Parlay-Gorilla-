import type { Metadata } from "next"
import { AiPicksHealthClient } from "./_components/AiPicksHealthClient"

export const metadata: Metadata = {
  title: "AI Picks Health | Internal",
  description: "Internal AI Picks health dashboard.",
  robots: "noindex, nofollow",
}

export default function AiPicksHealthPage() {
  return (
    <main className="min-h-screen bg-background">
      <AiPicksHealthClient />
    </main>
  )
}
