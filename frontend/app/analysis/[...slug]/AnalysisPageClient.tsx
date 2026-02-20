"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { motion } from "framer-motion"

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
  ConfidenceSection,
  MarketDisagreementBadge,
  PortfolioGuidancePanel,
  PropsPanel,
  DeltaSummary,
  MatchupIntelligencePanel,
  AnalysisHeaderStrip,
  HowThisAnalysisWasBuilt,
  TeamMatchupStatsPanel,
  UgieTopFactors,
  UgieAvailabilityImpact,
  UgieMatchupMismatches,
  UgieGameScript,
  UgieMarketEdge,
  UgieConfidenceRisk,
  UgieWeatherImpact,
  UgieDataQualityNotice,
  UgieFetchingBadge,
  UgieKeyPlayers,
} from "@/components/analysis/detail"
import { AnalysisDetailViewModelBuilder } from "@/lib/analysis/detail/AnalysisDetailViewModelBuilder"
import { SavedAnalysesManager } from "@/lib/analysis/detail/SavedAnalysesManager"
import { getVersionString } from "@/lib/constants/appVersion"
import { usePwaInstallNudge } from "@/lib/pwa/PwaInstallContext"
import { useSubscription } from "@/lib/subscription-context"
import { InlineUpgradeCta, AnalysisTrustFooter, MonetizationTimingSurface } from "@/components/conversion"
import {
  recordAnalysisView,
  recordVisit,
  setLastResearchAsOf,
  hasViewedSlug,
} from "@/lib/retention"
import {
  recordAnalysisView as recordIntentAnalysisView,
  emitIntentEvent,
} from "@/lib/monetization-timing"

function formatEnrichmentTime(isoString: string): string {
  try {
    const date = new Date(isoString)
    const now = new Date()
    const sec = Math.floor((now.getTime() - date.getTime()) / 1000)
    if (sec < 60) return "just now"
    if (sec < 3600) return `${Math.floor(sec / 60)} min ago`
    if (sec < 86400) return `${Math.floor(sec / 3600)} hours ago`
    if (sec < 604800) return `${Math.floor(sec / 86400)} days ago`
    return date.toLocaleDateString()
  } catch {
    return ""
  }
}

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
  const { isPremium, loading: subscriptionLoading } = useSubscription()

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
  const [previouslyViewed, setPreviouslyViewed] = useState(false)
  const [scrollCompleted, setScrollCompleted] = useState(false)
  const scrollSentinelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setIsSaved(SavedAnalysesManager.isSaved(analysis.slug))
  }, [analysis.slug])

  // Monetization timing: show upgrade surface only after user scrolls to bottom (never on load).
  useEffect(() => {
    const el = scrollSentinelRef.current
    if (!el) return
    const obs = new IntersectionObserver(
      ([e]) => {
        if (e?.isIntersecting) setScrollCompleted(true)
      },
      { rootMargin: "100px", threshold: 0.1 }
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  // Retention: count visit for streak
  useEffect(() => {
    recordVisit()
  }, [])

  // Retention: record view and check "Previously Viewed" before recording
  const confidenceForRetention =
    analysis.analysis_content?.model_win_probability?.ai_confidence ??
    viewModel.quickTake.confidencePercent
  useEffect(() => {
    setPreviouslyViewed(hasViewedSlug(analysis.slug))
    recordAnalysisView({
      slug: analysis.slug,
      sport,
      confidence: confidenceForRetention ?? undefined,
      matchup: analysis.matchup,
    })
    recordIntentAnalysisView(sport)
    emitIntentEvent("analysis_viewed", { sport })
    if (analysis.enrichment?.as_of) setLastResearchAsOf(analysis.enrichment.as_of)
  }, [analysis.slug, analysis.matchup, analysis.enrichment?.as_of, sport, confidenceForRetention])

  useEffect(() => {
    recordVisit()
  }, [])

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

          <motion.div
            className="container mx-auto px-4 py-6 max-w-6xl relative z-10 pb-28 md:pb-10"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
          >
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
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl md:text-3xl font-extrabold text-white leading-tight">
                  {pageTitle}
                </h1>
                {previouslyViewed && (
                  <span className="rounded-md border border-white/20 bg-white/5 px-2 py-0.5 text-xs font-medium text-white/70">
                    Previously Viewed
                  </span>
                )}
              </div>
              {viewModel.header.subtitle ? (
                <p className="text-sm text-white/60">{viewModel.header.subtitle}</p>
              ) : null}
              <p className="text-xs text-white/60">
                Updated in real time • {getVersionString()}
              </p>
            </div>

            {/* Pro analytics header strip: confidence, research depth, freshness, model status */}
            <AnalysisHeaderStrip
              confidencePercent={snippetAnswer.aiConfidencePct ?? viewModel.quickTake.confidencePercent ?? null}
              enrichment={analysis.enrichment ?? undefined}
              className="mb-4"
            />
            <p className="text-xs text-white/50 mb-4">
              AI tracking this matchup · Model monitoring trends · Research ongoing
            </p>
            {!subscriptionLoading && !isPremium && (
              <p className="text-xs text-white/50 mb-4">
                You&apos;re viewing limited analysis. Key edges hidden in free mode.
              </p>
            )}

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

            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1], delay: 0 }}
            >
              <FeaturedSnippetAnswer
                matchup={snippetAnswer.matchup}
                favoredTeam={snippetAnswer.favoredTeam}
                favoredWinPct={snippetAnswer.favoredWinPct}
                underdogTeam={snippetAnswer.underdogTeam}
                underdogWinPct={snippetAnswer.underdogWinPct}
                aiConfidencePct={snippetAnswer.aiConfidencePct}
                className="mb-4"
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1], delay: 0.2 }}
            >
              <QuickTakeCard
              sportIcon={viewModel.quickTake.sportIcon}
              favoredTeam={viewModel.quickTake.favoredTeam}
              confidencePercent={viewModel.quickTake.confidencePercent}
              confidenceLevel={viewModel.quickTake.confidenceLevel}
              riskLevel={viewModel.quickTake.riskLevel}
              recommendation={viewModel.quickTake.recommendation}
              whyText={viewModel.quickTake.whyText}
              limitedDataNote={viewModel.limitedDataNote}
              showConfidenceLocked={!isPremium}
            />
            {!subscriptionLoading && !isPremium && (
              <div className="mt-4">
                <InlineUpgradeCta variant="compact" />
              </div>
            )}
            </motion.div>

            <div className="hidden md:flex items-center gap-3 mt-4">
              <motion.button
                type="button"
                onClick={handleAddToParlay}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-emerald-500 to-green-500 text-black font-extrabold hover:from-emerald-400 hover:to-green-400 transition-all hover:shadow-lg hover:shadow-emerald-500/20"
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
              >
                Add to Parlay
              </motion.button>
              <motion.button
                type="button"
                onClick={handleSave}
                className="px-4 py-2 rounded-lg border border-white/15 bg-white/5 text-white font-extrabold hover:bg-white/10 hover:shadow-lg hover:shadow-white/5 transition-all"
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
              >
                {isSaved ? "Saved" : "Save"}
              </motion.button>
              <WatchButton gameId={analysis.game_id} />
              <motion.button
                type="button"
                onClick={handleShare}
                className="px-4 py-2 rounded-lg border border-white/15 bg-white/5 text-white font-extrabold hover:bg-white/10 hover:shadow-lg hover:shadow-white/5 transition-all"
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
              >
                Share
              </motion.button>
            </div>

            <motion.div
              className="mt-6 grid gap-5"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1], delay: 0.4 }}
            >
              {/* Delta Summary - Show what changed */}
              <DeltaSummary deltaSummary={analysis.analysis_content?.delta_summary} />

              {/* Matchup intelligence: standings, form, team stats, injuries (all sports) */}
              <MatchupIntelligencePanel
                enrichment={analysis.enrichment ?? undefined}
                unavailableReason={analysis.enrichment_unavailable_reason ?? undefined}
              />

              <KeyDriversList positives={viewModel.keyDrivers.positives} risks={viewModel.keyDrivers.risks} />

              <ProbabilityMeter
                teamA={viewModel.probability.teamA}
                teamB={viewModel.probability.teamB}
                probabilityA={viewModel.probability.probabilityA}
                probabilityB={viewModel.probability.probabilityB}
              />

              {/* New Intelligence Features — confidence gated by subscription + availability */}
              <ConfidenceSection
                isPremium={isPremium}
                analysisContent={analysis.analysis_content}
              />
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
                  ) : viewModel.ugieModules.rosterStatus !== undefined &&
                    (viewModel.ugieModules.rosterStatus === "missing" ||
                      viewModel.ugieModules.rosterStatus === "stale" ||
                      viewModel.ugieModules.rosterStatus === "unavailable") ? (
                    <UgieFetchingBadge
                      variant={viewModel.ugieModules.rosterStatus === "unavailable" ? "info" : viewModel.ugieModules.rosterStatus === "missing" ? "loading" : "info"}
                      label={
                        viewModel.ugieModules.rosterStatus === "unavailable"
                          ? "Roster unavailable"
                          : viewModel.ugieModules.rosterStatus === "missing"
                            ? "Fetching roster…"
                            : "Limited roster data"
                      }
                    />
                  ) : null}
                  {viewModel.ugieModules.availability || viewModel.ugieModules.injuriesStatus === "ready" || viewModel.ugieModules.injuriesStatus === "unavailable" || (viewModel.ugieModules.injuriesByTeam && (viewModel.ugieModules.injuriesByTeam.home?.length > 0 || viewModel.ugieModules.injuriesByTeam.away?.length > 0)) ? (
                    <UgieAvailabilityImpact
                      availability={viewModel.ugieModules.availability}
                      injuriesStatus={viewModel.ugieModules.injuriesStatus}
                      injuriesReason={viewModel.ugieModules.injuriesReason}
                      injuriesByTeam={viewModel.ugieModules.injuriesByTeam}
                      injuriesLastUpdatedAt={viewModel.ugieModules.injuriesLastUpdatedAt}
                    />
                  ) : (() => {
                    type Status = "ready" | "stale" | "missing" | "unavailable"
                    const status = viewModel.ugieModules.injuriesStatus as Status | undefined
                    const showBadge = status !== undefined &&
                      (status === "missing" || status === "stale" || status === "unavailable")
                    if (!showBadge) return null
                    return (
                      <UgieFetchingBadge
                        variant={status === "unavailable" ? "info" : status === "missing" ? "loading" : "info"}
                        label={
                          status === "unavailable"
                            ? "Injuries unavailable"
                            : status === "missing"
                              ? "Fetching injury data…"
                              : "Limited injury data"
                        }
                      />
                    )
                  })()}
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

              <HowThisAnalysisWasBuilt className="mt-6" />

              <div className="mt-6 rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-[11px] text-white/50 space-y-1">
                <p>Analyzing 1,000+ matchups weekly · Multi-league intelligence coverage · Continuous model monitoring</p>
              </div>

              <p className="mt-6 text-center text-sm text-white/60">
                Check back later — models update throughout the day.
              </p>

              <AnalysisTrustFooter
                updatedLabel={analysis.enrichment?.as_of ? formatEnrichmentTime(analysis.enrichment.as_of) : undefined}
                generatedLabel={analysis.generated_at ? formatEnrichmentTime(analysis.generated_at) : undefined}
                generatedAtIso={analysis.generated_at ?? undefined}
              />
              <div ref={scrollSentinelRef} className="h-1" aria-hidden />
              {!isPremium && !subscriptionLoading && (
                <MonetizationTimingSurface
                  context="after_analysis"
                  visible={scrollCompleted}
                  authResolved={!subscriptionLoading}
                  isPremium={isPremium}
                  analysisUpdated={!!analysis.enrichment?.as_of}
                  modelEdge={!!(analysis.analysis_content?.model_win_probability?.ai_confidence ?? viewModel.keyDrivers.positives?.length)}
                  researchDepth={analysis.enrichment ? "high" : undefined}
                  className="mt-6"
                />
              )}
            </motion.div>
          </motion.div>
        </main>
        <Footer />
      </div>

      <PrimaryActionBar onAddToParlay={handleAddToParlay} onSave={handleSave} isSaved={isSaved} />
    </div>
  )
}

