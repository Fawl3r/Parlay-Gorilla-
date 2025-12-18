"use client"

import { useMemo, useState } from "react"

import { GameAnalysisResponse } from "@/lib/api"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { SPORT_BACKGROUNDS } from "@/components/games/gamesConfig"
import { SportBackground } from "@/components/games/SportBackground"
import { MatchupHero } from "@/components/analysis/MatchupHero"
import { KeyNumbersBar } from "@/components/analysis/KeyNumbersBar"
import { GameBreakdown } from "@/components/analysis/GameBreakdown"
import { BestBetsSection } from "@/components/analysis/BestBetsSection"
import { SameGameParlays } from "@/components/analysis/SameGameParlays"
import { TrendsSection } from "@/components/analysis/TrendsSection"
import { WeatherInsights } from "@/components/analysis/WeatherInsights"
import { SnippetAnswerBlock } from "@/components/analysis/SnippetAnswerBlock"
import { SportsbookAdSlot, SportsbookInArticleAd, SportsbookStickyAd } from "@/components/ads/SportsbookAdSlot"
import { cn } from "@/lib/utils"
import Link from "next/link"
import { ArrowLeft, Share2 } from "lucide-react"

type TabId = "overview" | "breakdown" | "trends" | "picks" | "more"

export default function AnalysisPageClient({
  analysis,
  sport,
}: {
  analysis: GameAnalysisResponse
  sport: string
}) {
  const content = analysis.analysis_content
  const backgroundImage = SPORT_BACKGROUNDS[sport] || "/images/nflll.png"
  const hasWeather = Boolean(content.weather_considerations)
  const hasPicks = Boolean(content.same_game_parlays)
  const [activeTab, setActiveTab] = useState<TabId>("overview")

  const tabs = useMemo(() => {
    const next: Array<{ id: TabId; label: string }> = [
      { id: "overview", label: "Overview" },
      { id: "breakdown", label: "Full Breakdown" },
      { id: "trends", label: hasWeather ? "Trends + Weather" : "Trends" },
    ]
    if (hasPicks) next.push({ id: "picks", label: "Top Picks" })
    next.push({ id: "more", label: "More" })
    return next
  }, [hasPicks, hasWeather])

  const setTab = (tab: TabId) => {
    setActiveTab(tab)
    // Keep the background feeling “full-screen” by snapping back to the top when switching sections.
    if (typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" })
    }
  }

  const handleShare = async () => {
    if (navigator.share) {
      try {
        const shareText = (content.opening_summary || "").slice(0, 100)
        await navigator.share({
          title: `${analysis.matchup} - Game Analysis`,
          text: (shareText ? `${shareText}...` : "Game analysis"),
          url: window.location.href,
        })
      } catch {
        // Share cancelled by user
      }
    } else {
      // Fallback: copy to clipboard
      try {
        await navigator.clipboard.writeText(window.location.href)
      } catch {
        // Ignore clipboard errors (e.g. insecure context)
      }
    }
  }

  return (
    <div className="min-h-screen flex flex-col relative">
      <SportBackground imageUrl={backgroundImage} overlay="medium" />

      <div className="relative z-10 min-h-screen flex flex-col">
        <Header />
        <main className="flex-1">
          {/* Mobile Top Banner Ad */}
          <div className="md:hidden">
            <SportsbookAdSlot slotId="analysis-mobile-top" size="mobile-banner" className="my-2" />
          </div>

          <div className="container mx-auto px-4 py-6 max-w-6xl relative z-10">
            {/* Breadcrumb & Actions */}
            <div className="flex items-center justify-between gap-3 mb-4">
              <Link
                href="/analysis"
                className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                All Game Analyses
              </Link>
              <button
                onClick={handleShare}
                className="inline-flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground hover:text-primary border border-border rounded-lg transition-colors"
              >
                <Share2 className="h-4 w-4" />
                Share
              </button>
            </div>

            {/* Headline Section (compact) */}
            <div className="mb-5">
              <h1 className="text-2xl md:text-3xl lg:text-4xl font-extrabold text-foreground leading-tight mb-3">
                {content.headline || `${analysis.matchup.replace("@", "vs")} Predictions, Best Bets, Props & Odds`}
              </h1>
              {content.subheadline && (
                <p className="text-base md:text-lg text-muted-foreground leading-relaxed max-w-4xl">
                  {content.subheadline}
                </p>
              )}
            </div>

            {/* Compact section switcher (reduces default scroll) */}
            <div
              className="mb-6 flex items-center gap-2 overflow-x-auto rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm p-1"
              role="tablist"
              aria-label="Analysis sections"
            >
              {tabs.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTab(t.id)}
                  role="tab"
                  aria-selected={activeTab === t.id}
                  className={cn(
                    "px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap transition-colors",
                    activeTab === t.id ? "bg-emerald-500 text-black" : "text-gray-200 hover:bg-white/10"
                  )}
                >
                  {t.label}
                </button>
              ))}
            </div>

            <div className="grid gap-6 lg:grid-cols-[1fr,300px]">
              {/* Main Column */}
              <section className="min-w-0 space-y-5">
                {activeTab === "overview" ? (
                  <>
                    <SnippetAnswerBlock analysis={analysis} />

                    <MatchupHero
                      matchup={analysis.matchup}
                      league={analysis.league}
                      gameTime={analysis.game_time}
                      confidence={content.model_win_probability}
                    />

                    <div className="hidden md:block">
                      <SportsbookAdSlot slotId="analysis-leaderboard" size="leaderboard" className="my-4" />
                    </div>

                    <KeyNumbersBar
                      spreadPick={content.ai_spread_pick}
                      totalPick={content.ai_total_pick}
                      winProbability={content.model_win_probability}
                      matchup={analysis.matchup}
                    />

                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => setTab("breakdown")}
                        className="px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-gray-200 hover:bg-white/10 transition-colors text-sm font-semibold"
                      >
                        Full Breakdown
                      </button>
                      <button
                        type="button"
                        onClick={() => setTab("trends")}
                        className="px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-gray-200 hover:bg-white/10 transition-colors text-sm font-semibold"
                      >
                        Trends
                      </button>
                      {hasPicks ? (
                        <button
                          type="button"
                          onClick={() => setTab("picks")}
                          className="px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-gray-200 hover:bg-white/10 transition-colors text-sm font-semibold"
                        >
                          Top Picks
                        </button>
                      ) : null}
                      <button
                        type="button"
                        onClick={() => setTab("more")}
                        className="px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-gray-200 hover:bg-white/10 transition-colors text-sm font-semibold"
                      >
                        More
                      </button>
                    </div>

                    <BestBetsSection bestBets={content.best_bets} matchup={analysis.matchup} />

                    <div className="bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20 rounded-xl p-5 text-center">
                      <h3 className="text-lg font-bold mb-2">Want More Winning Picks?</h3>
                      <p className="text-muted-foreground mb-4">Build custom parlays with our AI-powered Parlay Builder</p>
                      <Link
                        href="/app"
                        className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-lg hover:from-emerald-400 hover:to-green-400 transition-all"
                      >
                        Try Parlay Builder Free
                      </Link>
                    </div>
                  </>
                ) : null}

                {activeTab === "breakdown" ? (
                  <>
                    <GameBreakdown content={content} />
                    <SportsbookInArticleAd slotId="analysis-in-article-1" />
                  </>
                ) : null}

                {activeTab === "trends" ? (
                  <>
                    <TrendsSection atsTrends={content.ats_trends} totalsTrends={content.totals_trends} matchup={analysis.matchup} />

                    {hasWeather ? (
                      <WeatherInsights weatherText={content.weather_considerations} weatherData={content.weather_data} />
                    ) : null}

                    <div className="lg:hidden">
                      <SportsbookAdSlot slotId="analysis-mobile-mid" size="rectangle" className="my-4" />
                    </div>
                  </>
                ) : null}

                {activeTab === "picks" ? (
                  hasPicks ? (
                    <>
                      <SameGameParlays parlays={content.same_game_parlays} />
                      <SportsbookInArticleAd slotId="analysis-in-article-2" />
                    </>
                  ) : (
                    <div className="rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm p-6 text-gray-300">
                      No same-game picks available yet for this matchup.
                    </div>
                  )
                ) : null}

                {activeTab === "more" ? (
                  <>
                    <div className="rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm p-6">
                      <h3 className="text-xl font-bold text-white mb-2">More {analysis.league} game analyses</h3>
                      <p className="text-gray-400 mb-4">Browse other matchups and open the full AI breakdown.</p>
                      <div className="flex flex-wrap gap-3">
                        <Link
                          href="/analysis"
                          className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-black font-semibold rounded-lg transition-colors"
                        >
                          View All Analyses →
                        </Link>
                        <Link
                          href="/sports"
                          className="inline-flex items-center justify-center gap-2 px-4 py-2 border border-white/20 hover:bg-white/10 text-white font-semibold rounded-lg transition-colors"
                        >
                          Browse Sports
                        </Link>
                      </div>
                    </div>

                    <SportsbookAdSlot slotId="analysis-bottom-banner" size="leaderboard" className="my-4" />
                  </>
                ) : null}
              </section>

              {/* Sidebar Column (Desktop) */}
              <aside className="hidden lg:block space-y-6">
                <SportsbookStickyAd slotId="analysis-sidebar-sticky" />
              </aside>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </div>
  )
}

