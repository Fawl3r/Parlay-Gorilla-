/**
 * Animation utilities and constants
 */

export const animationDurations = {
  fast: 150,
  normal: 200,
  slow: 300,
  slower: 400,
  slowest: 600,
} as const

export const animationEasings = {
  default: [0.4, 0, 0.2, 1] as [number, number, number, number],
  easeIn: [0.4, 0, 1, 1] as [number, number, number, number],
  easeOut: [0, 0, 0.2, 1] as [number, number, number, number],
  easeInOut: [0.4, 0, 0.2, 1] as [number, number, number, number],
  spring: { type: "spring" as const, stiffness: 300, damping: 30 },
  springBouncy: { type: "spring" as const, stiffness: 400, damping: 17 },
  springSmooth: { type: "spring" as const, stiffness: 200, damping: 25 },
} as const

export const staggerConfig = {
  container: {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
        delayChildren: 0.1,
      },
    },
  },
  item: {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0 },
  },
} as const

export const pageTransition = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
  transition: {
    duration: 0.2,
    ease: [0.4, 0, 0.2, 1],
  },
} as const

export const hoverScale = {
  whileHover: { scale: 1.02 },
  whileTap: { scale: 0.98 },
  transition: { type: "spring", stiffness: 400, damping: 17 },
} as const

export const cardHover = {
  whileHover: { y: -2, transition: { duration: 0.2 } },
} as const
