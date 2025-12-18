"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { Header } from "@/components/Header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { socialApi, SharedParlayDetail } from "@/lib/social-api"
import { Heart, ArrowLeft } from "lucide-react"

export default function SharedParlayPage() {
  const params = useParams<{ token: string }>()
  const [data, setData] = useState<SharedParlayDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      if (!params?.token) return
      setLoading(true)
      setError(null)
      try {
        const result = await socialApi.getSharedParlay(params.token)
        setData(result)
      } catch (err: any) {
        setError(err?.response?.data?.detail || "Unable to load shared parlay.")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [params?.token])

  const handleLike = async () => {
    if (!params?.token) return
    const result = await socialApi.toggleLike(params.token)
    setData((prev) =>
      prev
        ? {
            ...prev,
            shared: { ...prev.shared, is_liked: result.liked, likes_count: result.likes_count },
          }
        : prev
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      <Header />
      <main className="container mx-auto px-4 py-8 space-y-6">
        <div className="flex items-center gap-3">
          <Link href="/social" className="inline-flex items-center gap-2 text-primary hover:text-primary/80">
            <ArrowLeft className="h-4 w-4" />
            Back to social feed
          </Link>
        </div>

        {loading && <p className="text-muted-foreground text-sm">Loading shared parlay...</p>}
        {error && <p className="text-red-400 text-sm">{error}</p>}

        {data && (
          <Card className="bg-card/80 border-border/50">
            <CardHeader className="flex items-start justify-between">
              <div>
                <CardTitle className="text-xl text-foreground">
                  {data.parlay.num_legs}-Leg • {data.parlay.risk_profile.toUpperCase()}
                </CardTitle>
                <p className="text-sm text-muted-foreground">Shared by {data.user.display_name}</p>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="outline">Hit Prob: {(data.parlay.parlay_hit_prob * 100).toFixed(1)}%</Badge>
                  {data.shared.shared_at && (
                    <Badge variant="secondary">Shared {new Date(data.shared.shared_at).toLocaleDateString()}</Badge>
                  )}
                </div>
              </div>
              <Button variant="ghost" size="icon" onClick={handleLike}>
                <Heart
                  className={`h-5 w-5 ${
                    data.shared.is_liked ? "fill-rose-500 text-rose-500" : "text-muted-foreground"
                  }`}
                />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {data.shared.comment && <p className="text-sm text-muted-foreground">{data.shared.comment}</p>}
              {data.parlay.ai_summary && (
                <div className="p-4 rounded-lg border border-border/60 bg-muted/30">
                  <p className="text-sm text-foreground font-semibold mb-2">AI Summary</p>
                  <p className="text-sm text-muted-foreground whitespace-pre-line">{data.parlay.ai_summary}</p>
                </div>
              )}
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span>{data.shared.likes_count} likes</span>
                <span>{data.shared.views_count} views</span>
              </div>
              <Link href="/app" className="text-primary text-sm hover:text-primary/80">
                Build your own parlay
              </Link>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}

