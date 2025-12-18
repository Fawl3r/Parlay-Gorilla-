"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Header } from "@/components/Header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { socialApi, SharedParlayFeedItem, LeaderboardEntry } from "@/lib/social-api"
import { Badge } from "@/components/ui/badge"
import { Heart, ExternalLink, Users } from "lucide-react"
import { ProtectedRoute } from "@/components/ProtectedRoute"

function FeedItemCard({ item, onToggleLike }: { item: SharedParlayFeedItem; onToggleLike: (token: string) => void }) {
  return (
    <Card className="bg-card/80 border-border/50 hover:border-primary/40 transition-colors">
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Shared by {item.user.display_name}</p>
          <p className="text-lg font-semibold text-foreground">
            {item.parlay.num_legs}-Leg • {item.parlay.risk_profile.toUpperCase()}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="outline">Hit Prob: {(item.parlay.parlay_hit_prob * 100).toFixed(1)}%</Badge>
            {item.created_at && <Badge variant="secondary">Shared {new Date(item.created_at).toLocaleDateString()}</Badge>}
          </div>
        </div>
        <Button variant="ghost" size="icon" onClick={() => onToggleLike(item.share_token)}>
          <Heart className={`h-5 w-5 ${item.is_liked ? "fill-rose-500 text-rose-500" : "text-muted-foreground"}`} />
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {item.comment && <p className="text-sm text-muted-foreground">{item.comment}</p>}
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span>{item.likes_count} likes</span>
          <span>{item.views_count} views</span>
          <Link href={`/share/${item.share_token}`} className="inline-flex items-center gap-1 text-primary hover:text-primary/80">
            View details <ExternalLink className="h-3 w-3" />
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}

function LeaderboardCard({ entries }: { entries: LeaderboardEntry[] }) {
  return (
    <Card className="bg-card/80 border-border/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-4 w-4 text-primary" />
          Top Parlay Creators
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {entries.map((entry, index) => (
          <div key={entry.user_id} className="flex items-center justify-between rounded-lg border border-border/60 p-3">
            <div className="flex items-center gap-3">
              <Badge variant="outline">#{index + 1}</Badge>
              <div>
                <p className="font-semibold text-foreground">{entry.display_name}</p>
                <p className="text-xs text-muted-foreground">
                  {entry.total_parlays} parlays • {entry.high_prob_parlays} high-confidence
                </p>
              </div>
            </div>
            <Link href="/app" className="text-xs text-primary hover:text-primary/80">
              View parlays
            </Link>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export default function SocialPage() {
  const [feed, setFeed] = useState<SharedParlayFeedItem[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [loadingFeed, setLoadingFeed] = useState(false)
  const [loadingLeaderboard, setLoadingLeaderboard] = useState(false)

  useEffect(() => {
    const loadFeed = async () => {
      setLoadingFeed(true)
      try {
        const items = await socialApi.getFeed(25)
        setFeed(items)
      } finally {
        setLoadingFeed(false)
      }
    }

    const loadLeaderboard = async () => {
      setLoadingLeaderboard(true)
      try {
        const entries = await socialApi.getLeaderboard(10)
        setLeaderboard(entries)
      } finally {
        setLoadingLeaderboard(false)
      }
    }

    loadFeed()
    loadLeaderboard()
  }, [])

  const handleToggleLike = async (token: string) => {
    const result = await socialApi.toggleLike(token)
    setFeed((prev) =>
      prev.map((item) =>
        item.share_token === token
          ? { ...item, is_liked: result.liked, likes_count: result.likes_count }
          : item
      )
    )
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[#0a0a0f]">
        <Header />
        <main className="container mx-auto px-4 py-8 space-y-8">
          <div className="flex flex-col gap-4">
            <h1 className="text-3xl font-bold text-foreground">Community Feed</h1>
            <p className="text-muted-foreground">Share your parlays, gather likes, and see the top creators.</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              {loadingFeed && <p className="text-muted-foreground text-sm">Loading feed...</p>}
              {!loadingFeed && feed.length === 0 && (
                <Card className="bg-card/70 border-border/50">
                  <CardContent className="py-10 text-center text-muted-foreground">
                    No shared parlays yet. Share your first parlay from the builder to get started.
                  </CardContent>
                </Card>
              )}
              {feed.map((item) => (
                <FeedItemCard key={item.share_token} item={item} onToggleLike={handleToggleLike} />
              ))}
            </div>

            <div className="space-y-4">
              {loadingLeaderboard ? (
                <Card className="bg-card/70 border-border/50">
                  <CardContent className="py-6 text-center text-muted-foreground">Loading leaderboard...</CardContent>
                </Card>
              ) : (
                <LeaderboardCard entries={leaderboard} />
              )}
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}

