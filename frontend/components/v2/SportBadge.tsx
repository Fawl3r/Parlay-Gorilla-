/**
 * V2 Sport Badge Component
 * Sharp, terminal-style sport indicators
 */

import { Sport, getSportColor } from '@/lib/v2/mock-data'

interface SportBadgeProps {
  sport: Sport
  league: string
  size?: 'sm' | 'md'
}

export function SportBadge({ sport, league, size = 'md' }: SportBadgeProps) {
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 tracking-widest',
    md: 'text-xs px-2.5 py-1 tracking-widest',
  }

  return (
    <span
      className={`
        inline-flex items-center justify-center
        font-bold uppercase
        rounded-lg border border-[rgba(255,255,255,0.08)] bg-white/5
        ${getSportColor(sport)}
        ${sizeClasses[size]}
      `}
    >
      {league}
    </span>
  )
}
