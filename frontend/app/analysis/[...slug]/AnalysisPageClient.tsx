"use client"

import { GameAnalysisResponse } from "@/lib/api"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { MatchupHero } from "@/components/analysis/MatchupHero"
import { KeyNumbersBar } from "@/components/analysis/KeyNumbersBar"
import { GameBreakdown } from "@/components/analysis/GameBreakdown"
import { BestBetsSection } from "@/components/analysis/BestBetsSection"
import { SameGameParlays } from "@/components/analysis/SameGameParlays"
import { TrendsSection } from "@/components/analysis/TrendsSection"
import { WeatherInsights } from "@/components/analysis/WeatherInsights"
import { SnippetAnswerBlock } from "@/components/analysis/SnippetAnswerBlock"
import { AdSlot, InArticleAd, StickyAd } from "@/components/ads/AdSlot"
import Link from "next/link"
import { ArrowLeft, Share2 } from "lucide-react"

export default function AnalysisPageClient({ analysis }: { analysis: GameAnalysisResponse }) {
  const content = analysis.analysis_content

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `${analysis.matchup} - Game Analysis`,
          text: content.opening_summary.slice(0, 100) + "...",
          url: window.location.href,
        })
      } catch {
        // Share cancelled by user
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href)
    }
  }

  return (
    <div className="flex min-h-screen flex-col relative">
      <Header />
      <main className="flex-1 relative z-10">
        {/* Mobile Top Banner Ad */}
        <div className="md:hidden">
          <AdSlot slotId="analysis-mobile-top" size="mobile-banner" className="my-2" />
        </div>

        <div className="container mx-auto px-4 py-8 max-w-6xl relative z-10">
          {/* Breadcrumb & Actions */}
          <div className="flex items-center justify-between mb-6">
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

          {/* Headline Section */}
          <div className="mb-8">
            <h1 className="text-3xl md:text-4xl lg:text-5xl font-extrabold text-foreground leading-tight mb-4">
              {content.headline || `${analysis.matchup.replace('@', 'vs')} Predictions, Best Bets, Props & Odds`}
            </h1>
            {content.subheadline && (
              <p className="text-lg md:text-xl text-muted-foreground leading-relaxed max-w-4xl mb-6">
                {content.subheadline}
              </p>
            )}
          </div>

          {/* Snippet Answer Block - Optimized for Google Featured Snippets */}
          <SnippetAnswerBlock analysis={analysis} />

          {/* Matchup Hero Section with team logos */}
          <MatchupHero
            matchup={analysis.matchup}
            league={analysis.league}
            gameTime={analysis.generated_at}
            confidence={content.model_win_probability}
          />

          {/* Leaderboard Ad (Desktop) */}
          <div className="hidden md:block">
            <AdSlot slotId="analysis-leaderboard" size="leaderboard" className="my-6" />
          </div>

          {/* Key Numbers Bar */}
          <KeyNumbersBar
            spreadPick={content.ai_spread_pick}
            totalPick={content.ai_total_pick}
            winProbability={content.model_win_probability}
            matchup={analysis.matchup}
          />

          {/* Main Content Grid */}
          <div className="grid gap-8 lg:grid-cols-[1fr,300px] mt-8">
            {/* Main Content Column */}
            <div className="space-y-6 min-w-0">
              {/* Game Breakdown */}
              <GameBreakdown content={content} />

              {/* In-Article Ad after breakdown */}
              <InArticleAd slotId="analysis-in-article-1" />

              {/* Trends Section */}
              <TrendsSection
                atsTrends={content.ats_trends}
                totalsTrends={content.totals_trends}
                matchup={analysis.matchup}
              />

              {/* Weather Insights */}
              {content.weather_considerations && (
                <WeatherInsights 
                  weatherText={content.weather_considerations}
                  weatherData={content.weather_data}
                />
              )}

              {/* Rectangle Ad (Mobile only, between sections) */}
              <div className="lg:hidden">
                <AdSlot slotId="analysis-mobile-mid" size="rectangle" className="my-6" />
              </div>

              {/* Best Bets */}
              <BestBetsSection bestBets={content.best_bets} matchup={analysis.matchup} />

              {/* In-Article Ad before parlays */}
              <InArticleAd slotId="analysis-in-article-2" />

              {/* Same Game Parlays */}
              <SameGameParlays parlays={content.same_game_parlays} />

              {/* CTA Section */}
              <div className="bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20 rounded-xl p-6 text-center">
                <h3 className="text-xl font-bold mb-2">Want More Winning Picks?</h3>
                <p className="text-muted-foreground mb-4">
                  Build custom parlays with our AI-powered Parlay Builder
                </p>
                <Link
                  href="/app"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-lg hover:from-emerald-400 hover:to-green-400 transition-all"
                >
                  Try Parlay Builder Free
                </Link>
              </div>
            </div>

            {/* Sidebar Column (Desktop) */}
            <aside className="hidden lg:block space-y-6">
              {/* Sticky Sidebar Ad */}
              <StickyAd slotId="analysis-sidebar-sticky" />
            </aside>
          </div>

          {/* Bottom Banner Ad */}
          <AdSlot slotId="analysis-bottom-banner" size="leaderboard" className="my-8" />

          {/* Related Games Section */}
          <div className="mt-12 pt-8 border-t border-border">
            <h3 className="text-xl font-bold mb-4">More {analysis.league} Game Analyses</h3>
            <p className="text-muted-foreground mb-4">
              Check out our other expert breakdowns and picks
            </p>
            <Link
              href="/analysis"
              className="inline-flex items-center gap-2 text-primary hover:underline"
            >
              View All Analyses →
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  )
}

