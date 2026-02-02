"use client"

import { useEffect, useMemo, useState } from "react"

import { GameAnalysisResponse } from "@/lib/api"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { SPORT_BACKGROUNDS } from "@/components/games/gamesConfig"
import { SportBackground } from "@/components/games/SportBackground"
import { GameBreakdown } from "@/components/analysis/GameBreakdown"
import { SportsbookAdSlot } from "@/components/ads/SportsbookAdSlot"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowLeft, Share2 } from "lucide-react"
import { BalanceStrip } from "@/components/billing/BalanceStrip"
import { WatchButton } from "@/components/games/WatchButton"
import { toast } from "sonner"

import {
  AdvancedStatsAccordion,
  BetOptionsTabs,
  FeaturedSnippetAnswer,
  HeaderGameMatchup,
  KeyDriversList,
  MatchupBreakdownCard,
  PrimaryActionBar,
  ProbabilityMeter,
  QuickTakeCard,
  TrendsAccordion,
  OutcomePathsCard,
  ConfidenceBreakdownMeter,
  MarketDisagreementBadge,
  PortfolioGuidancePanel,
  PropsPanel,
  DeltaSummary,
  UgieTopFactors,
  UgieAvailabilityImpact,
  UgieMatchupMismatches,
  UgieGameScript,
  UgieMarketEdge,
  UgieConfidenceRisk,
  UgieWeatherImpact,
  UgieDataQualityNotice,
  UgieKeyPlayers,
} from "@/components/analysis/detail"
import { AnalysisDetailViewModelBuilder } from "@/lib/analysis/detail/AnalysisDetailViewModelBuilder"
import { SavedAnalysesManager } from "@/lib/analysis/detail/SavedAnalysesManager"
import { getVersionString } from "@/lib/constants/appVersion"
import { usePwaInstallNudge } from "@/lib/pwa/PwaInstallContext"

export default function AnalysisPageClient({
  analysis: initialAnalysis,
  sport,
}: {
  analysis: GameAnalysisResponse
  sport: string
}) {
  const router = useRouter()
  const [analysis, setAnalysis] = useState<GameAnalysisResponse>(initialAnalysis)
  const { nudgeInstallCta } = usePwaInstallNudge()

  useEffect(() => setAnalysis(initialAnalysis), [initialAnalysis])

  // Smart install nudge: when user views game analysis detail, allow CTA to re-appear
  useEffect(() => {
    nudgeInstallCta()
  }, [nudgeInstallCta])

  const backgroundImage = SPORT_BACKGROUNDS[sport] || "/images/nflll.png"

  const viewModel = useMemo(() => {
    return new AnalysisDetailViewModelBuilder().build({ analysis, sport })
  }, [analysis, sport])

  const pageTitle = analysis.seo_metadata?.title || `${analysis.matchup} Prediction & Picks`
  const modelProbs = analysis.analysis_content?.model_win_probability
  const snippetAnswer = useMemo(() => {
    const homeProb = Number(modelProbs?.home_win_prob ?? 0.5)
    const awayProb = Number(modelProbs?.away_win_prob ?? 0.5)

    const homeTeam = viewModel.header.homeTeam || "Home Team"
    const awayTeam = viewModel.header.awayTeam || "Away Team"

    const favoredIsHome = homeProb >= awayProb
    const favoredTeam = favoredIsHome ? homeTeam : awayTeam
    const underdogTeam = favoredIsHome ? awayTeam : homeTeam

    return {
      matchup: analysis.matchup,
      favoredTeam,
      favoredWinPct: Math.round(Math.max(homeProb, awayProb) * 100),
      underdogTeam,
      underdogWinPct: Math.round(Math.min(homeProb, awayProb) * 100),
      aiConfidencePct: modelProbs?.ai_confidence,
    }
  }, [
    analysis.matchup,
    viewModel.header.homeTeam,
    viewModel.header.awayTeam,
    modelProbs?.home_win_prob,
    modelProbs?.away_win_prob,
    modelProbs?.ai_confidence,
  ])

  const defaultBetTabId = viewModel.betOptions[0]?.id || "moneyline"
  const [activeBetTabId, setActiveBetTabId] = useState<string>(defaultBetTabId)
  useEffect(() => {
    setActiveBetTabId(defaultBetTabId)
  }, [defaultBetTabId])

  const [isSaved, setIsSaved] = useState(false)
  useEffect(() => {
    setIsSaved(SavedAnalysesManager.isSaved(analysis.slug))
  }, [analysis.slug])

  // Track page view for traffic-based props gating (client-side only)
  useEffect(() => {
    const trackView = async () => {
      try {
        const slugParts = analysis.slug.split("/")
        if (slugParts.length >= 2) {
          const sport = slugParts[0]
          const slug = slugParts.slice(1).join("/")
          await fetch(`/api/analysis/${sport}/${slug}/view`, {
            method: "POST",
          })
        }
      } catch (error) {
        // Silently fail - view tracking should never break the page
        console.debug("[Analysis] View tracking failed:", error)
      }
    }
    trackView()
  }, [analysis.slug])

  const handleShare = async () => {
    if (navigator.share) {
      try {
        const shareText = String(analysis.analysis_content?.opening_summary || "").slice(0, 100)
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

  const handleSave = () => {
    const next = SavedAnalysesManager.toggle(analysis.slug)
    setIsSaved(next)
    toast.success(next ? "Saved" : "Removed")
  }

  const handleAddToParlay = () => {
    nudgeInstallCta()
    const active = viewModel.betOptions.find((b) => b.id === activeBetTabId) ?? viewModel.betOptions[0]
    const prefill = active?.prefill

    const base = new URLSearchParams()
    base.set("tab", "custom-builder")
    if (prefill?.sport) base.set("sport", prefill.sport)
    if (prefill?.gameId) base.set("prefill_game_id", prefill.gameId)
    if (prefill?.marketType) base.set("prefill_market_type", prefill.marketType)
    if (prefill?.pick) base.set("prefill_pick", prefill.pick)
    if (prefill?.point !== undefined) base.set("prefill_point", String(prefill.point))

    router.push(`/app?${base.toString()}`)
  }

  return (
    <div className="min-h-screen flex flex-col relative">
      <SportBackground imageUrl={backgroundImage} overlay="medium" />

      <div className="relative z-10 min-h-screen flex flex-col">
        <Header onGenerate={handleAddToParlay} />
        <main className="flex-1">
          <div className="md:hidden">
            <SportsbookAdSlot slotId="analysis-mobile-top" size="mobile-banner" className="my-2" />
          </div>

          <div className="container mx-auto px-4 py-6 max-w-6xl relative z-10 pb-28 md:pb-10">
            <div className="flex items-center justify-between gap-3 mb-4">
              <Link
                href="/analysis"
                className="inline-flex items-center gap-2 text-sm text-white/70 hover:text-white transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </Link>
              <button
                onClick={handleShare}
                className="inline-flex items-center gap-2 px-3 py-2 text-sm text-white/70 hover:text-white border border-white/10 rounded-lg transition-colors"
              >
                <Share2 className="h-4 w-4" />
                Share
              </button>
            </div>

            <div className="mb-5 space-y-1">
              <h1 className="text-2xl md:text-3xl font-extrabold text-white leading-tight">
                {pageTitle}
              </h1>
              {viewModel.header.subtitle ? (
                <p className="text-sm text-white/60">{viewModel.header.subtitle}</p>
              ) : null}
              <p className="text-xs text-white/60">
                Updated in real time • {getVersionString()}
              </p>
            </div>

            <div className="md:hidden sticky top-16 z-40 space-y-2 mb-4">
              <HeaderGameMatchup
                title={viewModel.header.title}
                subtitle={viewModel.header.subtitle}
                lastUpdatedLabel={viewModel.header.lastUpdatedLabel}
                awayTeam={viewModel.header.awayTeam}
                homeTeam={viewModel.header.homeTeam}
                separator={viewModel.header.separator}
                sport={viewModel.header.sport}
              />
              <div className="rounded-xl border border-white/10 bg-black/40 backdrop-blur-sm p-2">
                <BalanceStrip compact />
              </div>
            </div>

            <div className="hidden md:block mb-6 space-y-3">
              <HeaderGameMatchup
                title={viewModel.header.title}
                subtitle={viewModel.header.subtitle}
                lastUpdatedLabel={viewModel.header.lastUpdatedLabel}
                awayTeam={viewModel.header.awayTeam}
                homeTeam={viewModel.header.homeTeam}
                separator={viewModel.header.separator}
                sport={viewModel.header.sport}
              />
              <BalanceStrip />
            </div>

            <FeaturedSnippetAnswer
              matchup={snippetAnswer.matchup}
              favoredTeam={snippetAnswer.favoredTeam}
              favoredWinPct={snippetAnswer.favoredWinPct}
              underdogTeam={snippetAnswer.underdogTeam}
              underdogWinPct={snippetAnswer.underdogWinPct}
              aiConfidencePct={snippetAnswer.aiConfidencePct}
              className="mb-4"
            />

            <QuickTakeCard
              sportIcon={viewModel.quickTake.sportIcon}
              favoredTeam={viewModel.quickTake.favoredTeam}
              confidencePercent={viewModel.quickTake.confidencePercent}
              confidenceLevel={viewModel.quickTake.confidenceLevel}
              riskLevel={viewModel.quickTake.riskLevel}
              recommendation={viewModel.quickTake.recommendation}
              whyText={viewModel.quickTake.whyText}
              limitedDataNote={viewModel.limitedDataNote}
            />

            <div className="hidden md:flex items-center gap-3 mt-4">
              <button
                type="button"
                onClick={handleAddToParlay}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-emerald-500 to-green-500 text-black font-extrabold hover:from-emerald-400 hover:to-green-400 transition-all"
              >
                Add to Parlay
              </button>
              <button
                type="button"
                onClick={handleSave}
                className="px-4 py-2 rounded-lg border border-white/15 bg-white/5 text-white font-extrabold hover:bg-white/10 transition-colors"
              >
                {isSaved ? "Saved" : "Save"}
              </button>
              <WatchButton gameId={analysis.game_id} />
              <button
                type="button"
                onClick={handleShare}
                className="px-4 py-2 rounded-lg border border-white/15 bg-white/5 text-white font-extrabold hover:bg-white/10 transition-colors"
              >
                Share
              </button>
            </div>

            <div className="mt-6 grid gap-5">
              {/* Delta Summary - Show what changed */}
              <DeltaSummary deltaSummary={analysis.analysis_content?.delta_summary} />

              <KeyDriversList positives={viewModel.keyDrivers.positives} risks={viewModel.keyDrivers.risks} />

              <ProbabilityMeter
                teamA={viewModel.probability.teamA}
                teamB={viewModel.probability.teamB}
                probabilityA={viewModel.probability.probabilityA}
                probabilityB={viewModel.probability.probabilityB}
              />

              {/* New Intelligence Features */}
              <ConfidenceBreakdownMeter confidenceBreakdown={analysis.analysis_content?.confidence_breakdown} />
              <OutcomePathsCard outcomePaths={analysis.analysis_content?.outcome_paths} />
              <MarketDisagreementBadge marketDisagreement={analysis.analysis_content?.market_disagreement} />
              <PortfolioGuidancePanel portfolioGuidance={analysis.analysis_content?.portfolio_guidance} />
              <PropsPanel propRecommendations={analysis.analysis_content?.prop_recommendations} />

              <BetOptionsTabs
                tabs={viewModel.betOptions.map((b) => ({
                  id: b.id,
                  label: b.label,
                  option: {
                    lean: b.lean,
                    confidenceLevel: b.confidenceLevel,
                    riskLevel: b.riskLevel,
                    explanation: b.explanation,
                  },
                }))}
                activeTabId={activeBetTabId}
                onTabChange={(id) => setActiveBetTabId(String(id))}
              />

              {viewModel.ugieModules ? (
                <>
                  <UgieTopFactors topFactors={viewModel.ugieModules.topFactors} />
                  {viewModel.keyPlayers ? (
                    <UgieKeyPlayers
                      keyPlayers={viewModel.keyPlayers}
                      homeTeamName={viewModel.header.homeTeam}
                      awayTeamName={viewModel.header.awayTeam}
                    />
                  ) : null}
                  <UgieAvailabilityImpact availability={viewModel.ugieModules.availability} />
                  <UgieMatchupMismatches matchupMismatches={viewModel.ugieModules.matchupMismatches} />
                  <UgieGameScript gameScript={viewModel.ugieModules.gameScript} />
                  <UgieMarketEdge marketEdge={viewModel.ugieModules.marketEdge} />
                  <UgieConfidenceRisk confidenceRisk={viewModel.ugieModules.confidenceRisk} />
                  <UgieWeatherImpact weather={viewModel.ugieModules.weather} />
                  <UgieDataQualityNotice dataQualityNotice={viewModel.ugieModules.dataQualityNotice} />
                </>
              ) : (
                viewModel.matchupCards.map((card, idx) => (
                  <MatchupBreakdownCard
                    key={`${card.title}-${idx}`}
                    title={card.title}
                    summary={card.summary}
                    bulletInsights={card.bulletInsights}
                  />
                ))
              )}

              <TrendsAccordion trends={viewModel.trends} />

              <AdvancedStatsAccordion>
                <GameBreakdown content={analysis.analysis_content} />
              </AdvancedStatsAccordion>
            </div>
          </div>
        </main>
        <Footer />
      </div>

      <PrimaryActionBar onAddToParlay={handleAddToParlay} onSave={handleSave} isSaved={isSaved} />
    </div>
  )
}

