/**
 * V2 Glass Card — V1 glass vibe + sharp chamfer (no bubble)
 */

import { ReactNode } from 'react'

interface GlassCardProps {
  children: ReactNode
  className?: string
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hover?: boolean
  /** Set false in scroll-heavy areas (e.g. landing pick strip) to avoid backdrop-blur jank */
  blur?: boolean
}

export function GlassCard({
  children,
  className = '',
  padding = 'md',
  hover = false,
  blur = true,
}: GlassCardProps) {
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-5',
  }
  const surfaceClass = blur
    ? 'bg-[rgba(18,18,23,0.6)] backdrop-blur-[10px]'
    : 'bg-[rgba(18,18,23,0.85)]'

  return (
    <div
      className={`
        ${surfaceClass}
        border border-[rgba(255,255,255,0.08)]
        rounded-[8px]
        ${paddingClasses[padding]}
        ${hover
          ? 'hover:border-[#00FF5E]/30 hover:-translate-y-0.5 cursor-pointer v2-card-hover'
          : 'v2-transition-colors'}
        ${className}
      `}
    >
      {children}
    </div>
  )
}
