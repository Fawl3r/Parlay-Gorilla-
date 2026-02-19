/**
 * V2 Odds Chip — V1 accent + rectangular (no pill)
 */

import { formatOdds } from '@/lib/v2/mock-data'

interface OddsChipProps {
  odds: number
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'positive' | 'negative'
  onClick?: () => void
}

export function OddsChip({ odds, size = 'md', variant = 'default', onClick }: OddsChipProps) {
  const sizeClasses = {
    sm: 'text-xs px-2 py-1 tracking-tight',
    md: 'text-sm px-3 py-1 tracking-tight',
    lg: 'text-base px-4 py-1.5 tracking-tight',
  }

  const variantClasses = {
    default: 'bg-white/5 text-white/90 border border-[rgba(255,255,255,0.08)]',
    positive: 'bg-[#00FF5E]/10 text-[#00FF5E] border border-[#00FF5E]/40',
    negative: 'bg-red-500/10 text-red-400 border border-red-500/40',
  }

  return (
    <span
      className={`
        inline-flex items-center justify-center font-bold tabular-nums
        rounded-lg border-l-2
        transition-colors duration-150
        ${onClick ? 'cursor-pointer v2-hover-lift v2-press-scale hover:border-[#00FF5E]/50' : ''}
        ${sizeClasses[size]}
        ${variantClasses[variant]}
      `}
      onClick={onClick}
    >
      {formatOdds(odds)}
    </span>
  )
}
