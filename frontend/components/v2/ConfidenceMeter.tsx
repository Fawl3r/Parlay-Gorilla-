/**
 * V2 Confidence Meter Component
 * Sharp, terminal-style confidence indicator with animation
 */

'use client'

import { useEffect, useState } from 'react'
import { getConfidenceColor, getConfidenceBgColor } from '@/lib/v2/mock-data'
import { prefersReducedMotion } from '@/lib/v2/motion'

interface ConfidenceMeterProps {
  confidence: number
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function ConfidenceMeter({
  confidence,
  showLabel = true,
  size = 'md',
}: ConfidenceMeterProps) {
  const [animatedValue, setAnimatedValue] = useState(0)

  useEffect(() => {
    if (prefersReducedMotion()) {
      setAnimatedValue(confidence)
      return
    }

    const timeout = setTimeout(() => {
      setAnimatedValue(confidence)
    }, 100)

    return () => clearTimeout(timeout)
  }, [confidence])

  const heightClasses = {
    sm: 'h-1',
    md: 'h-1',
    lg: 'h-2',
  }

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  }

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex items-center justify-between mb-1.5">
          <span 
            className={`
              font-bold uppercase tracking-tight 
              ${getConfidenceColor(confidence)} 
              ${textSizeClasses[size]}
            `}
          >
            {confidence}%
          </span>
          <span className="text-xs text-white/50 uppercase tracking-wider">CONF</span>
        </div>
      )}
      <div className="w-full bg-white/5 border border-[rgba(255,255,255,0.08)] rounded-lg">
        <div
          className={`
            ${getConfidenceBgColor(confidence)} 
            ${heightClasses[size]} 
            rounded-lg transition-[width] duration-[240ms]
          `}
          style={{ 
            width: `${animatedValue}%`,
            transitionTimingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        />
      </div>
    </div>
  )
}
