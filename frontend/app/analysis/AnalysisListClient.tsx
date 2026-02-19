"use client"

import { useEffect, useState } from "react"
import { api, GameAnalysisListItem } from "@/lib/api"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { SportsbookAdSlot, SportsbookInArticleAd } from "@/components/ads/SportsbookAdSlot"
import { Loader2, AlertCircle, TrendingUp, Calendar, Trophy } from "lucide-react"
import Link from "next/link"
import { motion } from "framer-motion"
import { getCopy } from "@/lib/content"
import { useSportsAvailability } from "@/lib/sports/useSportsAvailability"
import { SPORT_NAMES, SPORT_ICONS } from "@/components/games/gamesConfig"
import { cn } from "@/lib/utils"

export default function AnalysisListClient() {
  const [selectedSport, setSelectedSport] = useState("nfl")
  const [analyses, setAnalyses] = useState<GameAnalysisListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { sports, error: sportsError, isStale: sportsStale, isSportEnabled, getSportBadge, normalizeSlug } = useSportsAvailability()
  const selectedSportName = sports.find((s) => normalizeSlug(s.slug) === selectedSport)?.display_name || SPORT_NAMES[selectedSport] || selectedSport.toUpperCase()

  // If selected sport becomes disabled, switch to first enabled
  useEffect(() => {
    if (sports.length === 0) return
    if (isSportEnabled(selectedSport)) return
    const firstEnabled = sports.find((s) => isSportEnabled(normalizeSlug(s.slug)))
    if (firstEnabled) {
      const slug = normalizeSlug(firstEnabled.slug)
      if (slug && slug !== selectedSport) setSelectedSport(slug)
    }
  }, [sports, selectedSport, isSportEnabled, normalizeSlug])

  useEffect(() => {
    async function fetchAnalyses() {
      try {
        setLoading(true)
        setError(null)
        const data = await api.listUpcomingAnalyses(selectedSport, 50)
        setAnalyses(data)
      } catch (err: unknown) {
        console.error("Error fetching analyses:", err)
        const message = err instanceof Error ? err.message : "Failed to load analyses"
        setError(message)
      } finally {
        setLoading(false)
      }
    }

    fetchAnalyses()
  }, [selectedSport])

  // Group analyses by date
  const groupedAnalyses = analyses.reduce((groups, analysis) => {
    const date = new Date(analysis.game_time).toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
    })
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(analysis)
    return groups
  }, {} as Record<string, GameAnalysisListItem[]>)

  const groupedEntries = Object.entries(groupedAnalyses)

  return (
    <div className="flex min-h-screen flex-col relative">
      <Header />
      <main className="flex-1 relative z-10">
        {/* Hero Section */}
        <section className="py-16 relative">
          <div className="container relative z-10 px-4">
            <motion.div 
              className="mb-8 text-center"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-4">
                <TrendingUp className="h-4 w-4 text-emerald-400" />
                <span className="text-sm font-medium text-emerald-400">AI-Powered Analysis</span>
              </div>
              <h1 className="mb-3 text-4xl font-extrabold tracking-tight sm:text-5xl">
                <span className="gradient-text">Game Analysis & Predictions</span>
              </h1>
              <p className="text-lg text-foreground/90 max-w-2xl mx-auto font-medium">
                Expert AI-powered game breakdowns, best bets, and parlay recommendations
              </p>
            </motion.div>

            {/* Top Banner Ad */}
            <SportsbookAdSlot slotId="analysis-list-top" size="leaderboard" className="mb-8" />

            {/* Sport Selector — from backend; disabled when is_enabled === false */}
            {sportsError && (
              <div className="mb-8 py-4 text-center text-destructive font-medium">
                Couldn&apos;t reach backend. Try refresh.
                {sportsStale && (
                  <div className="text-xs mt-1 text-muted-foreground">
                    Showing last saved sports list. <span className="text-[10px] uppercase tracking-wide text-muted-foreground/80" aria-label="Stale data">Stale data</span>
                  </div>
                )}
              </div>
            )}
            {/* Sport selector: is_enabled from backend is the ONLY enable/disable rule; no local season logic. */}
            {sports.length > 0 && (
              <div className="mb-8 flex flex-wrap justify-center gap-3">
                {sports.map((s) => {
                  const slug = normalizeSlug(s.slug)
                  const enabled = isSportEnabled(slug)
                  const disabled = !enabled
                  const label = s.display_name || SPORT_NAMES[slug] || slug.toUpperCase()
                  const icon = SPORT_ICONS[slug] ?? "•"
                  const badge = getSportBadge(slug)
                  return (
                    <motion.button
                      key={slug}
                      onClick={() => (disabled ? undefined : setSelectedSport(slug))}
                      disabled={disabled}
                      className={cn(
                        "px-6 py-3 rounded-xl border-2 transition-all font-semibold flex flex-col items-center gap-1",
                        selectedSport === slug
                          ? "border-primary bg-primary/10 text-primary shadow-lg shadow-primary/20"
                          : "border-border text-muted-foreground hover:border-primary/50 hover:bg-primary/5",
                        disabled && "opacity-40 cursor-not-allowed"
                      )}
                      title={disabled ? badge || "Not in season" : undefined}
                      whileHover={!disabled ? { scale: 1.02 } : undefined}
                      whileTap={!disabled ? { scale: 0.98 } : undefined}
                    >
                      <span className="flex items-center gap-2">
                        <span>{icon}</span>
                        <span>{label}</span>
                      </span>
                      {disabled && badge ? <span className="text-xs opacity-80">{badge}</span> : null}
                    </motion.button>
                  )
                })}
              </div>
            )}

            {/* Stats Bar */}
            <div className="grid grid-cols-3 gap-4 max-w-2xl mx-auto mb-8">
              <div className="text-center p-4 rounded-lg bg-card/50 border border-border">
                <div className="text-2xl font-bold text-primary">{analyses.length}</div>
                <div className="text-xs text-muted-foreground">Upcoming Games</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-card/50 border border-border">
                <div className="text-2xl font-bold text-emerald-400">Free</div>
                <div className="text-xs text-muted-foreground">All Analysis</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-card/50 border border-border">
                <div className="text-2xl font-bold text-cyan-400">AI</div>
                <div className="text-xs text-muted-foreground">Powered Picks</div>
              </div>
            </div>

            {/* Loading State */}
            {loading && (
              <Card>
                <CardContent className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <span className="ml-3 text-muted-foreground">{getCopy("states.loading.loadingAnalyses")}</span>
                </CardContent>
              </Card>
            )}

            {/* Error State */}
            {error && (
              <Card className="border-destructive/50">
                <CardContent className="flex items-center justify-center gap-3 py-12">
                  <AlertCircle className="h-8 w-8 text-destructive" />
                  <div>
                    <h3 className="font-semibold text-destructive">{getCopy("states.errors.loadFailed")}</h3>
                    <p className="text-sm text-muted-foreground">{error}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Empty State */}
            {!loading && !error && analyses.length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Trophy className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground text-lg">
                    {getCopy("states.empty.noAnalyses")}
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Analysis List */}
            {!loading && !error && analyses.length > 0 && (
              <div className="space-y-8">
                {groupedEntries.map(([date, dateAnalyses], groupIndex) => (
                  <div key={date}>
                    {/* Date Header */}
                    <div className="flex items-center gap-3 mb-4">
                      <Calendar className="h-5 w-5 text-primary" />
                      <h2 className="text-lg font-bold">{date}</h2>
                      <div className="flex-1 h-px bg-border" />
                      <span className="text-sm text-muted-foreground">
                        {dateAnalyses.length} game{dateAnalyses.length !== 1 ? "s" : ""}
                      </span>
                    </div>

                    {/* Games Grid */}
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                      {dateAnalyses.map((analysis, index) => (
                        <motion.div
                          key={analysis.id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.3, delay: index * 0.05 }}
                        >
                          <Link
                            href={`/analysis/${analysis.slug}`}
                            className="block group"
                          >
                            <Card className="h-full hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 transition-all duration-300 overflow-hidden">
                              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-green-500 to-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                              <CardHeader className="pb-2">
                                <div className="flex items-start justify-between">
                                  <CardTitle className="text-lg group-hover:text-primary transition-colors">
                                    {analysis.matchup}
                                  </CardTitle>
                                  <span className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary font-medium">
                                    {analysis.league}
                                  </span>
                                </div>
                                <CardDescription className="flex items-center gap-2">
                                  <span>{new Date(analysis.game_time).toLocaleTimeString("en-US", {
                                    hour: "numeric",
                                    minute: "2-digit",
                                  })}</span>
                                </CardDescription>
                              </CardHeader>
                              <CardContent>
                                <div className="flex items-center justify-between">
                                  <span className="text-xs text-muted-foreground">
                                    Analysis ready
                                  </span>
                                  <span className="text-xs text-primary font-medium group-hover:underline">
                                    View Breakdown →
                                  </span>
                                </div>
                              </CardContent>
                            </Card>
                          </Link>
                        </motion.div>
                      ))}
                    </div>

                    {/* Insert ads after every 2nd group */}
                    {(groupIndex + 1) % 2 === 0 && groupIndex < groupedEntries.length - 1 && (
                      <SportsbookInArticleAd slotId={`analysis-list-mid-${groupIndex}`} className="my-8" />
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Bottom Ad */}
            <SportsbookAdSlot slotId="analysis-list-bottom" size="leaderboard" className="mt-12" />

            {/* CTA Section */}
            <div className="mt-12 text-center">
              <Card className="bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border-emerald-500/20">
                <CardContent className="py-8">
                  <h3 className="text-2xl font-bold mb-2">Gorilla Parlay Builder</h3>
                  <p className="text-muted-foreground mb-4 max-w-md mx-auto">
                    Use our AI-powered Parlay Builder to create winning combinations
                  </p>
                  <Link
                    href="/app"
                    className="inline-flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-lg hover:from-emerald-400 hover:to-green-400 transition-all shadow-lg shadow-emerald-500/25"
                  >
                    Try Parlay Builder Free
                  </Link>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar Rectangle Ad (visible on larger screens) */}
            <div className="hidden xl:block fixed right-4 top-1/2 -translate-y-1/2 z-40">
              <SportsbookAdSlot slotId="analysis-list-sidebar" size="rectangle" />
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}

