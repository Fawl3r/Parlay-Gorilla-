/**
 * V2 MOTION UTILITIES
 * Edgy, trading-terminal style animations
 * GPU-friendly, respects reduced-motion
 */

// Check if user prefers reduced motion
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

// Standard transition timings
export const TRANSITIONS = {
  fast: '120ms',
  normal: '180ms',
  slow: '300ms',
} as const

// Easing functions
export const EASING = {
  smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
  sharp: 'cubic-bezier(0.4, 0, 1, 1)',
  spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
} as const

// Page transition variants
export const pageTransition = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: {
    duration: prefersReducedMotion() ? 0 : 0.18,
    ease: EASING.smooth,
  },
}

// Hover scale
export const hoverScale = {
  scale: prefersReducedMotion() ? 1 : 1.01,
  transition: { duration: 0.12 },
}

// Press scale
export const pressScale = {
  scale: prefersReducedMotion() ? 1 : 0.98,
  transition: { duration: 0.1 },
}

// Stagger children
export const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: prefersReducedMotion() ? 0 : 0.05,
    },
  },
}

// Fade in item
export const fadeInItem = {
  initial: { opacity: 0, y: 4 },
  animate: { opacity: 1, y: 0 },
  transition: {
    duration: prefersReducedMotion() ? 0 : 0.15,
  },
}
