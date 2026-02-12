"use client"

import { useEffect, useRef } from "react"
import { AnimatePresence } from "framer-motion"
import { Crown, Lock } from "lucide-react"
import { PaywallModal, type PaywallReason } from "@/components/paywall/PaywallModal"

import { GameCard } from "@/components/custom-parlay/GameCard"
import { CustomParlayAnalysisModal } from "@/components/custom-parlay/AnalysisModal"
import { CoveragePackModal } from "@/components/custom-parlay/CoveragePackModal"
import { HedgePackModal } from "@/components/custom-parlay/HedgePackModal"
import { ParlaySlip } from "@/components/custom-parlay/ParlaySlip"
import type { SelectedPick } from "@/components/custom-parlay/types"
import type { TemplateId } from "@/lib/custom-parlay/templateEngine"
import type { CounterLegCandidate, CounterParlayMode, CustomParlayAnalysisResponse, DerivedTicket, GameResponse, ParlayCoverageResponse, UpsetPossibilities } from "@/lib/api"
import type { PaywallError } from "@/lib/subscription-context"
import { sportsUiPolicy } from "@/lib/sports/SportsUiPolicy"

export type SportOption = { id: string; name: string; icon: string }

export type BuilderAccessSummary = {
  builderTier: "free" | "premium" | "unknown"
  freeCustomRemaining?: number | null
  premiumCustomRemaining?: number | null
  creditsRemaining?: number | null
}

export type CustomParlayBuilderViewProps = {
  userPresent: boolean
  canUseCustomBuilder: boolean
  isCreditUser: boolean
  isPremium: boolean
  builderAccessSummary?: BuilderAccessSummary

  sports: readonly SportOption[]
  selectedSport: string
  inSeasonBySport: Record<string, boolean>
  onSelectSport: (sportId: string) => void

  games: GameResponse[]
  loading: boolean
  error: string | null

  selectedPicks: SelectedPick[]
  onSelectPick: (pick: SelectedPick) => void
  onRemovePick: (index: number) => void
  onClearSlip?: () => void
  onApplyTemplate?: (templateId: TemplateId) => void

  onAnalyze: () => void
  isAnalyzing: boolean
  onSave: (title?: string) => void
  isSaving: boolean

  onGenerateCounter: () => void
  isGeneratingCounter: boolean
  counterMode: CounterParlayMode
  onCounterModeChange: (mode: CounterParlayMode) => void
  counterTargetLegs: number
  onCounterTargetLegsChange: (value: number) => void

  onGenerateCoveragePack: () => void
  isGeneratingCoveragePack: boolean
  coveragePack: ParlayCoverageResponse | null
  hedgeCoveragePack: DerivedTicket[] | null
  hedgeUpsetPossibilities: UpsetPossibilities | null
  isCoverageModalOpen: boolean
  onCloseCoverageModal: () => void
  onHedgeApplyClicked?: (ticket: DerivedTicket) => void
  coverageMaxTotalParlays: number
  coverageScenarioMax: number
  coverageRoundRobinMax: number
  coverageRoundRobinSize: number
  onCoverageMaxTotalParlaysChange: (value: number) => void
  onCoverageScenarioMaxChange: (value: number) => void
  onCoverageRoundRobinMaxChange: (value: number) => void
  onCoverageRoundRobinSizeChange: (value: number) => void

  analysis: CustomParlayAnalysisResponse | null
  counterAnalysis: CustomParlayAnalysisResponse | null
  counterCandidates: CounterLegCandidate[] | null
  isModalOpen: boolean
  onCloseModal: () => void

  showPaywall: boolean
  paywallReason: PaywallReason
  paywallError: PaywallError | null
  onOpenPaywall: () => void
  onClosePaywall: () => void
  creditsOverlayDismissed?: boolean
  onDismissCreditsOverlay?: () => void
  templateFollowThroughTrigger?: boolean
  isBeginnerMode?: boolean
  onFollowThroughShown?: () => void
}

function resolveSportName(sports: readonly SportOption[], id: string): string {
  return sports.find((s) => s.id === id)?.name || "Games"
}

export function CustomParlayBuilderView(props: CustomParlayBuilderViewProps) {
  const sportName = resolveSportName(props.sports, props.selectedSport)
  const summary = props.builderAccessSummary
  const credits = summary?.creditsRemaining ?? 0
  const tier = summary?.builderTier ?? "unknown"
  const hasCredits = typeof credits === "number" && credits > 0

  const slipRef = useRef<HTMLDivElement>(null)
  const followThroughShownRef = useRef(false)
  const { templateFollowThroughTrigger, isBeginnerMode, onFollowThroughShown } = props

  useEffect(() => {
    if (templateFollowThroughTrigger && slipRef.current) {
      slipRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" })
    }
  }, [templateFollowThroughTrigger])

  useEffect(() => {
    if (
      templateFollowThroughTrigger &&
      isBeginnerMode &&
      !followThroughShownRef.current &&
      typeof sessionStorage !== "undefined" &&
      !sessionStorage.getItem("pg_template_followthrough_shown")
    ) {
      followThroughShownRef.current = true
      sessionStorage.setItem("pg_template_followthrough_shown", "1")
      onFollowThroughShown?.()
    }
  }, [templateFollowThroughTrigger, isBeginnerMode, onFollowThroughShown])

  const blockedNoCredits = props.userPresent && !props.canUseCustomBuilder && !hasCredits
  const hasCreditsButNoAccess = props.userPresent && !props.canUseCustomBuilder && hasCredits

  if (blockedNoCredits) {
    const isFree = tier === "free"
    const title = isFree ? "Weekly limit reached" : "Included analyses used"
    const body = isFree
      ? "You've used your free Custom Builder analyses for now. You can try again later, buy credits, or upgrade for more."
      : "You've used your included Custom Builder analyses for this period. Buy credits or wait for the reset."
    return (
      <>
        <div className="min-h-screen p-6 relative">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm z-10 flex items-center justify-center">
            <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl border border-emerald-500/30 p-8 max-w-md text-center shadow-2xl">
              <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-6">
                <Lock className="h-8 w-8 text-emerald-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">{title}</h2>
              <p className="text-gray-400 mb-6">{body}</p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={props.onOpenPaywall}
                  className="py-3 px-6 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-emerald-500/30 transition-all flex items-center justify-center gap-2"
                >
                  <Crown className="h-5 w-5" />
                  Upgrade
                </button>
                <a
                  href="/pricing#credits"
                  className="py-3 px-6 bg-white/10 text-white font-bold rounded-xl border border-white/20 hover:bg-white/15 transition-all flex items-center justify-center"
                >
                  Buy credits
                </a>
              </div>
            </div>
          </div>
          <div className="filter blur-sm pointer-events-none">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-2">Gorilla Parlay Builder 🦍</h1>
              <p className="text-white/60 max-w-2xl mx-auto">
                Select your picks and get AI-powered analysis with probability estimates and confidence scores
              </p>
            </div>
          </div>
        </div>

        <PaywallModal isOpen={props.showPaywall} onClose={props.onClosePaywall} reason={props.paywallReason} error={props.paywallError} />
      </>
    )
  }

  if (hasCreditsButNoAccess && !props.creditsOverlayDismissed) {
    return (
      <>
        <div className="min-h-screen p-6 relative">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm z-10 flex items-center justify-center">
            <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl border border-emerald-500/30 p-8 max-w-md text-center shadow-2xl">
              <h2 className="text-xl font-bold text-white mb-2">Use credits to continue</h2>
              <p className="text-gray-400 mb-6">
                You have credits available. Custom Builder analyses will use credits when your free or included ones are used.
              </p>
              <button
                onClick={() => props.onDismissCreditsOverlay?.()}
                className="w-full py-3 px-6 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-xl hover:shadow-lg transition-all"
              >
                Continue
              </button>
            </div>
          </div>
          <div className="filter blur-sm pointer-events-none opacity-60">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-2">Gorilla Parlay Builder 🦍</h1>
            </div>
          </div>
        </div>
      </>
    )
  }

  const showPills = summary && (summary.premiumCustomRemaining != null || summary.freeCustomRemaining != null || summary.creditsRemaining != null)

  return (
    <>
      <div className="min-h-screen p-6" data-testid="pg-builder-root" data-page="custom-builder">
        <div className="text-center mb-8">
          <div className="flex flex-col items-center gap-2 mb-2">
            <div className="flex items-center justify-center gap-2 flex-wrap">
              <h1 className="text-4xl font-bold text-white">Gorilla Parlay Builder 🦍</h1>
              {props.isPremium && (
                <span className="bg-gradient-to-r from-emerald-500 to-green-500 text-black text-xs font-bold px-2 py-1 rounded-full">
                  <Crown className="h-3 w-3 inline mr-1" />
                  Premium
                </span>
              )}
            </div>
            {showPills && summary && (
              <div className="flex items-center justify-center gap-2 flex-wrap">
                {summary.builderTier === "premium" && summary.premiumCustomRemaining != null && (
                  <span className="bg-white/10 text-white/80 text-xs px-2.5 py-1 rounded-full">
                    Included analyses left: {summary.premiumCustomRemaining}
                  </span>
                )}
                {summary.builderTier === "free" && summary.freeCustomRemaining != null && (
                  <span className="bg-white/10 text-white/80 text-xs px-2.5 py-1 rounded-full">
                    Free analyses left: {summary.freeCustomRemaining}
                  </span>
                )}
                {summary.creditsRemaining != null && (
                  <span className="bg-white/10 text-white/80 text-xs px-2.5 py-1 rounded-full">
                    Credits: {summary.creditsRemaining}
                  </span>
                )}
              </div>
            )}
          </div>
          <p className="text-white/60 max-w-2xl mx-auto">
            Pick your plays, then get AI analysis and confidence in one tap.
          </p>
        </div>

        <div className="flex justify-center gap-2 mb-8 flex-wrap">
          {props.sports.map((sport) => {
            const isComingSoon = sportsUiPolicy.isComingSoon(sport.id)
            const isDisabled = props.inSeasonBySport[sport.id] === false || isComingSoon
            const disabledLabel = isComingSoon ? "Coming Soon" : "Not in season"

            return (
              <button
                key={sport.id}
                onClick={() => props.onSelectSport(sport.id)}
                disabled={isDisabled}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  props.selectedSport === sport.id
                    ? "bg-primary text-primary-foreground"
                    : isDisabled
                      ? "bg-white/5 text-white/30 cursor-not-allowed"
                      : "bg-white/10 text-white/70 hover:bg-white/15"
                }`}
                title={isDisabled ? disabledLabel : undefined}
              >
                {sport.icon} {sport.name}
                {isDisabled ? (
                  <span className="ml-2 text-[10px] font-bold uppercase">{disabledLabel}</span>
                ) : null}
              </button>
            )
          })}
        </div>

        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4" data-custom-builder-games>
            <h2 className="text-xl font-bold text-white">{sportName} Games</h2>

            {props.loading && (
              <div className="flex items-center justify-center py-12" data-testid="pg-loading">
                <span className="text-4xl">🦍</span>
              </div>
            )}

            {props.error && (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-400">{props.error}</div>
            )}

            {!props.loading && !props.error && props.games.length === 0 && (
              <div className="text-center text-white/60 py-12">No games available for {sportName}</div>
            )}

            {!props.loading &&
              props.games.map((game) => (
                <GameCard 
                  key={game.id} 
                  game={game} 
                  onSelectPick={props.onSelectPick} 
                  selectedPicks={props.selectedPicks}
                  isPremium={props.isPremium}
                />
              ))}
          </div>

          <div className="lg:col-span-1 space-y-4" ref={slipRef}>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <h3 className="text-white font-semibold text-sm mb-1">Quick start</h3>
              <p className="text-white/60 text-xs mb-3">Tap a style — we&apos;ll fill your slip with picks.</p>
              {props.templateFollowThroughTrigger && props.isBeginnerMode && (
                <p className="text-emerald-400/90 text-xs mb-3" data-template-helper>
                  Next: tap Analyze to get your AI breakdown.
                </p>
              )}
              <div className="flex flex-col gap-2">
                <button
                  type="button"
                  data-testid="pg-add-pick"
                  disabled={props.loading || !props.games.length}
                  onClick={() => props.onApplyTemplate?.("safer_2")}
                  className="w-full py-2.5 px-3 rounded-lg border border-white/20 bg-white/5 text-white text-sm font-medium hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-left"
                >
                  Safer 2-Pick
                </button>
                <button
                  type="button"
                  disabled={props.loading || !props.games.length}
                  onClick={() => props.onApplyTemplate?.("solid_3")}
                  className="w-full py-2.5 px-3 rounded-lg border border-white/20 bg-white/5 text-white text-sm font-medium hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-left"
                >
                  Solid 3-Pick
                </button>
                <button
                  type="button"
                  disabled={props.loading || !props.games.length}
                  onClick={() => props.onApplyTemplate?.("longshot_4")}
                  className="w-full py-2.5 px-3 rounded-lg border border-white/20 bg-white/5 text-white text-sm font-medium hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-left"
                >
                  Longshot 4-Pick
                </button>
              </div>
            </div>
            <ParlaySlip
              picks={props.selectedPicks}
              onRemovePick={props.onRemovePick}
              onClearSlip={props.onClearSlip}
              templatePulseAnalyze={props.templateFollowThroughTrigger}
              onAnalyze={props.onAnalyze}
              isAnalyzing={props.isAnalyzing}
              onSave={props.onSave}
              isSaving={props.isSaving}
              onGenerateCounter={props.onGenerateCounter}
              isGeneratingCounter={props.isGeneratingCounter}
              counterMode={props.counterMode}
              onCounterModeChange={props.onCounterModeChange}
              counterTargetLegs={props.counterTargetLegs}
              onCounterTargetLegsChange={props.onCounterTargetLegsChange}
              onGenerateCoveragePack={props.onGenerateCoveragePack}
              isGeneratingCoveragePack={props.isGeneratingCoveragePack}
              coverageMaxTotalParlays={props.coverageMaxTotalParlays}
              coverageScenarioMax={props.coverageScenarioMax}
              coverageRoundRobinMax={props.coverageRoundRobinMax}
              coverageRoundRobinSize={props.coverageRoundRobinSize}
              onCoverageMaxTotalParlaysChange={props.onCoverageMaxTotalParlaysChange}
              onCoverageScenarioMaxChange={props.onCoverageScenarioMaxChange}
              onCoverageRoundRobinMaxChange={props.onCoverageRoundRobinMaxChange}
              onCoverageRoundRobinSizeChange={props.onCoverageRoundRobinSizeChange}
            />
          </div>
        </div>

        <AnimatePresence>
          {props.isModalOpen && props.analysis && (
            <CustomParlayAnalysisModal
              analysis={props.analysis}
              counterAnalysis={props.counterAnalysis}
              counterCandidates={props.counterCandidates}
              onClose={props.onCloseModal}
            />
          )}
        </AnimatePresence>

        <AnimatePresence>
          {props.isCoverageModalOpen && props.coveragePack && (
            <CoveragePackModal response={props.coveragePack} onClose={props.onCloseCoverageModal} />
          )}
          {props.isCoverageModalOpen && (props.hedgeCoveragePack?.length || 0) > 0 && (
            <HedgePackModal
              tickets={props.hedgeCoveragePack ?? []}
              upsetPossibilities={props.hedgeUpsetPossibilities}
              onClose={props.onCloseCoverageModal}
              onApplyTicket={props.onHedgeApplyClicked}
            />
          )}
        </AnimatePresence>
      </div>

      <PaywallModal isOpen={props.showPaywall} onClose={props.onClosePaywall} reason={props.paywallReason} error={props.paywallError} />
    </>
  )
}


