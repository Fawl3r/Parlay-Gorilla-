/**
 * V2 Glass Card — V1 glass vibe + sharp chamfer (no bubble)
 */

import { ReactNode } from 'react'

interface GlassCardProps {
  children: ReactNode
  className?: string
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hover?: boolean
}

export function GlassCard({ children, className = '', padding = 'md', hover = false }: GlassCardProps) {
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-5',
  }

  return (
    <div
      className={`
        bg-[rgba(18,18,23,0.6)] backdrop-blur-[10px]
        border border-[rgba(255,255,255,0.08)]
        rounded-lg
        v2-transition-colors
        ${paddingClasses[padding]}
        ${hover ? 'v2-hover-sweep hover:border-white/[0.12] hover:border-[#00FF5E]/30' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  )
}
