/**
 * V2 Pick Card Component
 * Sharp, terminal-style pick display
 */

import { MockPick } from '@/lib/v2/mock-data'
import { GlassCard } from './GlassCard'
import { SportBadge } from './SportBadge'
import { OddsChip } from './OddsChip'
import { ConfidenceMeter } from './ConfidenceMeter'

interface PickCardProps {
  pick: MockPick
  variant?: 'compact' | 'full'
  onSelect?: () => void
}

export function PickCard({ pick, variant = 'full', onSelect }: PickCardProps) {
  if (variant === 'compact') {
    return (
      <GlassCard
        className="min-w-[280px] cursor-pointer"
        padding="md"
        hover
        blur={false}
      >
        <div className="flex flex-col gap-2" onClick={onSelect}>
          <div className="flex items-center justify-between">
            <SportBadge sport={pick.sport} league={pick.league} size="sm" />
            {pick.aiGenerated && (
              <span className="text-xs font-bold text-[#00FF5E] bg-[#00FF5E]/10 px-2 py-0.5 rounded-lg border border-[#00FF5E]/40 uppercase tracking-wider">
                AI
              </span>
            )}
          </div>
          
          <div className="border-l-2 border-[rgba(255,255,255,0.08)] pl-2">
            <p className="text-xs text-white/50 mb-0.5 uppercase tracking-wide">{pick.matchup}</p>
            <p className="text-sm font-bold text-white uppercase tracking-tight">{pick.pick}</p>
          </div>

          <div className="flex items-center justify-between pt-1">
            <OddsChip odds={pick.odds} size="sm" />
            <span className="text-sm font-bold text-[#00FF5E] uppercase tracking-tight tabular-nums">
              {pick.confidence}%
            </span>
          </div>
        </div>
      </GlassCard>
    )
  }

  return (
    <GlassCard padding="md" hover={!!onSelect} className={onSelect ? 'cursor-pointer' : ''}>
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <SportBadge sport={pick.sport} league={pick.league} />
          {pick.aiGenerated && (
            <span className="text-xs font-bold text-[#00FF5E] bg-[#00FF5E]/10 px-2 py-1 rounded-lg border border-[#00FF5E]/40 uppercase tracking-wider">
              AI PICK
            </span>
          )}
        </div>

        <div className="border-l-2 border-[rgba(255,255,255,0.08)] pl-3">
          <p className="text-xs text-white/50 mb-1 uppercase tracking-wide">{pick.matchup}</p>
          <p className="text-lg font-bold text-white mb-0.5 uppercase tracking-tight">{pick.pick}</p>
          <p className="text-xs text-white/40 uppercase tracking-wider">{pick.pickType}</p>
        </div>

        <div className="flex items-center gap-4 pt-1">
          <OddsChip odds={pick.odds} />
          <span className="text-xs text-white/40 uppercase tracking-wider">
            {new Date(pick.gameTime).toLocaleTimeString('en-US', {
              hour: 'numeric',
              minute: '2-digit',
            })}
          </span>
        </div>

        <ConfidenceMeter confidence={pick.confidence} />
      </div>
    </GlassCard>
  )
}
