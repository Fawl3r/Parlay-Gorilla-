"use client"

import { useEffect, useState } from "react"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import Link from "next/link"
import { ArrowLeft, TrendingUp } from "lucide-react"

interface TopEdge {
  game_id: string
  matchup: string
  sport: string
  start_time: string
  confidence_total: number
  model_edge_pct: number
  edge_score: number
  analysis_slug: string
}

interface TopEdgesResponse {
  top_edges: TopEdge[]
  count: number
}

export default function TopEdgesPage() {
  const [edges, setEdges] = useState<TopEdge[]>([])
  const [loading, setLoading] = useState(true)
  const [sport, setSport] = useState<string>("")

  useEffect(() => {
    const fetchTopEdges = async () => {
      try {
        const params = new URLSearchParams()
        if (sport) params.append("sport", sport)
        params.append("limit", "20")

        const response = await fetch(`/api/analytics/top-edges?${params.toString()}`)
        if (!response.ok) throw new Error("Failed to fetch top edges")

        const data: TopEdgesResponse = await response.json()
        setEdges(data.top_edges || [])
      } catch (error) {
        console.error("Error fetching top edges:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchTopEdges()
  }, [sport])

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-gray-900 to-black">
      <Header />
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-white/60 hover:text-white transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
          <h1 className="text-3xl font-extrabold text-white mb-2">Top Betting Edges</h1>
          <p className="text-white/60">Games with the highest confidence and model edge</p>
        </div>

        <div className="mb-4">
          <select
            value={sport}
            onChange={(e) => setSport(e.target.value)}
            className="px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white"
          >
            <option value="">All Sports</option>
            <option value="NFL">NFL</option>
            <option value="NBA">NBA</option>
            <option value="NHL">NHL</option>
            <option value="MLB">MLB</option>
          </select>
        </div>

        {loading ? (
          <div className="text-white/60">Loading...</div>
        ) : edges.length === 0 ? (
          <div className="text-white/60">No edges found</div>
        ) : (
          <div className="grid gap-4">
            {edges.map((edge) => (
              <Link
                key={edge.game_id}
                href={`/analysis/${edge.analysis_slug}`}
                className="block rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm p-5 hover:bg-black/40 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-lg font-bold text-white mb-1">{edge.matchup}</h3>
                    <div className="text-sm text-white/60">{edge.sport}</div>
                  </div>
                  <div className="flex items-center gap-2 text-green-500">
                    <TrendingUp className="w-5 h-5" />
                    <span className="text-xl font-bold">{edge.edge_score.toFixed(1)}</span>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-white/60">Confidence</div>
                    <div className="text-white font-semibold">{edge.confidence_total.toFixed(0)}%</div>
                  </div>
                  <div>
                    <div className="text-white/60">Model Edge</div>
                    <div className="text-white font-semibold">+{edge.model_edge_pct.toFixed(1)}%</div>
                  </div>
                  <div>
                    <div className="text-white/60">Start Time</div>
                    <div className="text-white font-semibold">
                      {new Date(edge.start_time).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
      <Footer />
    </div>
  )
}
