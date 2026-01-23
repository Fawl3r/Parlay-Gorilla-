"use client"

import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { api, WinWallResponse } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Loader2 } from "lucide-react"

type TabType = "AI" | "CUSTOM" | "ALL"

export function WinWall() {
  const [activeTab, setActiveTab] = useState<TabType>("ALL")
  const [wins, setWins] = useState<WinWallResponse[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchWins = async () => {
      setLoading(true)
      try {
        const data = await api.getWinWall(50, activeTab)
        setWins(data)
      } catch (error) {
        console.error("Error fetching win wall:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchWins()
    const interval = setInterval(fetchWins, 30000) // Refresh every 30 seconds

    return () => clearInterval(interval)
  }, [activeTab])

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-4">Win Wall</h2>
        <p className="text-gray-400">Celebrating parlay wins from the community</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/10">
        {(["ALL", "AI", "CUSTOM"] as TabType[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === tab
                ? "text-emerald-400 border-b-2 border-emerald-400"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {tab === "ALL" ? "All Wins" : tab === "AI" ? "AI Parlays" : "Gorilla Builder"}
          </button>
        ))}
      </div>

      {/* Wins Grid */}
      {loading ? (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
        </div>
      ) : wins.length === 0 ? (
        <div className="text-center py-20 text-gray-400">No wins to display yet</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {wins.map((win, index) => (
            <motion.div
              key={win.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="bg-white/5 border border-white/10 rounded-xl p-4"
            >
              <div className="flex items-start justify-between mb-2">
                <Badge
                  variant="outline"
                  className={
                    win.parlay_type === "AI"
                      ? "bg-blue-500/20 text-blue-300 border-blue-500/30"
                      : "bg-purple-500/20 text-purple-300 border-purple-500/30"
                  }
                >
                  {win.parlay_type === "AI" ? "AI Parlay" : "Custom"}
                </Badge>
                <span className="text-xs text-gray-500">
                  {new Date(win.settled_at).toLocaleTimeString()}
                </span>
              </div>

              <div className="text-lg font-bold text-white mb-2">{win.summary}</div>

              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-gray-400">{win.legs_count} legs</span>
                  <span className="text-emerald-400 font-medium">{win.odds}</span>
                </div>
                {win.user_alias && (
                  <span className="text-gray-500 text-xs">{win.user_alias}</span>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
