"use client"

import { useEffect, useState } from "react"
import { api, GameResponse } from "@/lib/api"
import { Header } from "@/components/Header"
import { Hero } from "@/components/Hero"
import { Footer } from "@/components/Footer"
import { GameCard } from "@/components/GameCard"
import { GameFilters } from "@/components/GameFilters"
import { ParlayBuilder } from "@/components/ParlayBuilder"
import { Card, CardContent } from "@/components/ui/card"
import { Loader2, AlertCircle } from "lucide-react"

export default function Home() {
  const [games, setGames] = useState<GameResponse[]>([])
  const [filteredGames, setFilteredGames] = useState<GameResponse[]>([])
  const [selectedSportsbook, setSelectedSportsbook] = useState<string>("all")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchGames() {
      try {
        setLoading(true)
        setError(null)
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        console.log('Fetching games from:', apiUrl)
        
        // First check if backend is reachable
        try {
          const healthCheck = await api.healthCheck()
          console.log('Backend health check:', healthCheck)
        } catch (healthErr) {
          console.error('Backend health check failed:', healthErr)
          setError('Backend server is not reachable. Make sure it is running on port 8000.')
          setLoading(false)
          return
        }
        
        const data = await api.getNFLGames()
        console.log('Games received:', data.length)
        setGames(data)
        setFilteredGames(data) // Initialize filtered games
      } catch (err: unknown) {
        console.error('Error fetching games:', err)
        const detail =
          typeof err === "object" && err !== null && "response" in err
            ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
            : undefined
        const fallback = err instanceof Error ? err.message : "Failed to fetch games"
        setError(`Error: ${detail || fallback}`)
      } finally {
        setLoading(false)
      }
    }

    fetchGames()
  }, [])

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <Hero />

        {/* Parlay Builder Section */}
        <section id="builder" className="py-20 relative">
          <div className="absolute inset-0 dark-overlay-strong z-0" />
          <div className="container relative z-10 px-4">
            <div className="mb-12 text-center">
              <h2 className="mb-3 text-4xl font-extrabold tracking-tight sm:text-5xl">
                <span className="gradient-text">Parlay Builder</span>
              </h2>
              <p className="text-lg text-foreground/90 max-w-2xl mx-auto font-medium">
                Generate optimized parlays with AI-powered recommendations and real-time probability calculations
              </p>
            </div>
            <ParlayBuilder />
          </div>
        </section>

        {/* Games Section */}
        <section id="games" className="border-t-2 border-primary/30 py-20 relative">
          <div className="absolute inset-0 dark-overlay-strong z-0" />
          <div className="container px-4">
            <div className="mb-10 relative z-10">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="mb-3 text-4xl font-extrabold tracking-tight sm:text-5xl">
                    <span className="gradient-text-accent">Upcoming Games</span>
                  </h2>
                  {!loading && !error && games.length > 0 && (
                    <p className="text-foreground/80 text-lg font-semibold">
                      Showing <span className="font-bold text-foreground">{filteredGames.length}</span> of <span className="font-bold text-foreground">{games.length}</span> game{games.length !== 1 ? 's' : ''}
                    </p>
                  )}
                </div>
                {!loading && !error && filteredGames.length > 0 && (() => {
                  const weeks = [...new Set(filteredGames.map(g => g.week).filter(w => w != null))].sort((a, b) => (a || 0) - (b || 0))
                  if (weeks.length > 0) {
                    return (
                      <div className="rounded-xl border-2 border-primary/40 bg-gradient-to-r from-primary/20 to-secondary/20 px-6 py-3 backdrop-blur-sm team-badge neon-glow-effect">
                        <div className="text-sm font-bold">
                          {weeks.length === 1 ? (
                            <span className="gradient-text">Week {weeks[0]}</span>
                          ) : (
                            <span className="gradient-text-accent">Weeks {weeks[0]} - {weeks[weeks.length - 1]}</span>
                          )}
                        </div>
                      </div>
                    )
                  }
                  return null
                })()}
              </div>
            </div>

            {/* Filters */}
            {!loading && !error && games.length > 0 && (
              <GameFilters
                games={games}
                onFilterChange={setFilteredGames}
                onSportsbookChange={setSelectedSportsbook}
              />
            )}

            {loading && (
              <Card>
                <CardContent className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-muted-foreground">Loading games...</span>
                </CardContent>
              </Card>
            )}

            {error && (
              <Card>
                <CardContent className="flex items-center justify-center py-12">
                  <AlertCircle className="h-8 w-8 text-destructive" />
                  <div className="ml-4">
                    <h3 className="font-semibold text-destructive">Error loading games</h3>
                    <p className="text-sm text-muted-foreground">{error}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {!loading && !error && games.length === 0 && (
              <Card>
                <CardContent className="flex items-center justify-center py-12">
                  <p className="text-muted-foreground">No upcoming games found</p>
                </CardContent>
              </Card>
            )}

            {!loading && !error && filteredGames.length === 0 && games.length > 0 && (
              <Card>
                <CardContent className="flex items-center justify-center py-12">
                  <p className="text-muted-foreground">
                    No games match the selected filters. Try adjusting your filters.
                  </p>
                </CardContent>
              </Card>
            )}

            {!loading && !error && filteredGames.length > 0 && (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {filteredGames.map((game) => (
                  <GameCard
                    key={game.id}
                    game={game}
                    selectedSportsbook={selectedSportsbook}
                  />
                ))}
              </div>
            )}
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}

