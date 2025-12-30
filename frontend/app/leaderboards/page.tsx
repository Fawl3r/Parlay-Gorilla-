import { Header } from "@/components/Header"
import { LeaderboardsPageClient } from "@/app/leaderboards/LeaderboardsPageClient"

export default function LeaderboardsPage() {
  return (
    <div className="min-h-screen">
      <Header />
      <LeaderboardsPageClient />
    </div>
  )
}


