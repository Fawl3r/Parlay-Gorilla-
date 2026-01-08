"use client"

import { AnimatePresence } from "framer-motion"
import { Crown, Lock } from "lucide-react"
import { PaywallModal, type PaywallReason } from "@/components/paywall/PaywallModal"

import { GameCard } from "@/components/custom-parlay/GameCard"
import { CustomParlayAnalysisModal } from "@/components/custom-parlay/AnalysisModal"
import { CoveragePackModal } from "@/components/custom-parlay/CoveragePackModal"
import { ParlaySlip } from "@/components/custom-parlay/ParlaySlip"
import type { SelectedPick } from "@/components/custom-parlay/types"
import type { CounterLegCandidate, CounterParlayMode, CustomParlayAnalysisResponse, GameResponse, ParlayCoverageResponse } from "@/lib/api"
import type { PaywallError } from "@/lib/subscription-context"
import { sportsUiPolicy } from "@/lib/sports/SportsUiPolicy"

export type SportOption = { id: string; name: string; icon: string }

export type CustomParlayBuilderViewProps = {
  userPresent: boolean
  canUseCustomBuilder: boolean
  isCreditUser: boolean
  isPremium: boolean

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
  isCoverageModalOpen: boolean
  onCloseCoverageModal: () => void
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
}

function resolveSportName(sports: readonly SportOption[], id: string): string {
  return sports.find((s) => s.id === id)?.name || "Games"
}

export function CustomParlayBuilderView(props: CustomParlayBuilderViewProps) {
  const sportName = resolveSportName(props.sports, props.selectedSport)

  if (!props.canUseCustomBuilder && !props.isCreditUser && props.userPresent) {
    return (
      <>
        <div className="min-h-screen p-6 relative">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm z-10 flex items-center justify-center">
            <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl border border-emerald-500/30 p-8 max-w-md text-center shadow-2xl">
              <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-6">
                <Lock className="h-8 w-8 text-emerald-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Premium Subscription Required</h2>
              <p className="text-gray-400 mb-6">
                The 🦍 Gorilla Parlay Builder 🦍 requires Gorilla Premium or credits. Upgrade to Premium for daily access, or buy credits to use AI actions on your custom builds.
              </p>
              <button
                onClick={props.onOpenPaywall}
                className="w-full py-3 px-6 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-emerald-500/30 transition-all flex items-center justify-center gap-2"
              >
                <Crown className="h-5 w-5" />
                Unlock Premium
              </button>
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

  return (
    <>
      <div className="min-h-screen p-6">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <h1 className="text-4xl font-bold text-white">AI Parlay Builder 🦍</h1>
            {props.isPremium && (
              <span className="bg-gradient-to-r from-emerald-500 to-green-500 text-black text-xs font-bold px-2 py-1 rounded-full">
                <Crown className="h-3 w-3 inline mr-1" />
                Premium
              </span>
            )}
          </div>
          <p className="text-white/60 max-w-2xl mx-auto">
            Select your picks and generate a counter ticket to spot upsets / value against your assumptions.
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
                    ? "bg-[#00FF5E] text-black"
                    : isDisabled
                      ? "bg-white/5 text-white/30 cursor-not-allowed"
                      : "bg-white/10 text-white/70 hover:bg-[#00FF5E]/20"
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
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-xl font-bold text-white">{sportName} Games</h2>

            {props.loading && (
              <div className="flex items-center justify-center py-12">
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
                <GameCard key={game.id} game={game} onSelectPick={props.onSelectPick} selectedPicks={props.selectedPicks} />
              ))}
          </div>

          <div className="lg:col-span-1">
            <ParlaySlip
              picks={props.selectedPicks}
              onRemovePick={props.onRemovePick}
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
        </AnimatePresence>
      </div>

      <PaywallModal isOpen={props.showPaywall} onClose={props.onClosePaywall} reason={props.paywallReason} error={props.paywallError} />
    </>
  )
}


