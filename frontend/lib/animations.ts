import { Variants } from "framer-motion"

/**
 * Reusable Framer Motion animation variants for the neon UI
 */

// Page Transitions
export const pageTransition: Variants = {
  initial: { opacity: 0, scale: 0.95, y: 20 },
  animate: { opacity: 1, scale: 1, y: 0 },
  exit: { opacity: 0, scale: 0.95, y: -20 },
}

export const fadeIn: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
}

export const slideUp: Variants = {
  initial: { opacity: 0, y: 50 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -50 },
}

export const slideDown: Variants = {
  initial: { opacity: 0, y: -50 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 50 },
}

export const slideLeft: Variants = {
  initial: { opacity: 0, x: 50 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -50 },
}

export const slideRight: Variants = {
  initial: { opacity: 0, x: -50 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 50 },
}

// Scale Animations
export const scaleIn: Variants = {
  initial: { opacity: 0, scale: 0.8 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.8 },
}

export const scaleUp: Variants = {
  initial: { scale: 1 },
  animate: { scale: 1.05 },
}

// Card Animations
export const cardHover: Variants = {
  initial: { scale: 1, rotateY: 0 },
  animate: { scale: 1.02, rotateY: 5 },
}

export const cardFlip: Variants = {
  initial: { rotateY: 0 },
  animate: { rotateY: 180 },
}

export const cardTilt: Variants = {
  initial: { rotateX: 0, rotateY: 0 },
  animate: { rotateX: -5, rotateY: 5 },
}

// Stagger Children
export const staggerContainer: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
}

export const staggerItem: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: "easeOut",
    },
  },
}

// Neon Glow Effects
export const neonPulse: Variants = {
  initial: { filter: "brightness(1)" },
  animate: {
    filter: ["brightness(1)", "brightness(1.3)", "brightness(1)"],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "easeInOut",
    },
  },
}

export const glowRipple: Variants = {
  initial: { scale: 0, opacity: 0.8 },
  animate: {
    scale: 2,
    opacity: 0,
    transition: {
      duration: 0.6,
      ease: "easeOut",
    },
  },
}

// Button Animations
export const buttonPress: Variants = {
  initial: { scale: 1 },
  tap: { scale: 0.95 },
  hover: { scale: 1.05 },
}

export const buttonGlow: Variants = {
  initial: { boxShadow: "0 0 20px hsl(150 100% 50% / 0.3)" },
  hover: {
    boxShadow: "0 0 30px hsl(150 100% 50% / 0.6), 0 0 50px hsl(150 100% 50% / 0.4)",
    transition: { duration: 0.3 },
  },
}

// Loading Animations
export const spin: Variants = {
  animate: {
    rotate: 360,
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: "linear",
    },
  },
}

export const float: Variants = {
  animate: {
    y: [-10, 10, -10],
    transition: {
      duration: 3,
      repeat: Infinity,
      ease: "easeInOut",
    },
  },
}

export const pulse: Variants = {
  animate: {
    scale: [1, 1.1, 1],
    opacity: [1, 0.7, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "easeInOut",
    },
  },
}

// Text Animations
export const textReveal: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: "easeOut",
    },
  },
}

export const textGlow: Variants = {
  initial: { textShadow: "0 0 10px hsl(150 100% 50% / 0.5)" },
  animate: {
    textShadow: [
      "0 0 10px hsl(150 100% 50% / 0.5)",
      "0 0 20px hsl(150 100% 50% / 0.8)",
      "0 0 10px hsl(150 100% 50% / 0.5)",
    ],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "easeInOut",
    },
  },
}

// Micro-interactions
export const bounce: Variants = {
  initial: { y: 0 },
  animate: {
    y: [-5, 5, -5, 0],
    transition: {
      duration: 0.5,
      ease: "easeOut",
    },
  },
}

export const shake: Variants = {
  initial: { x: 0 },
  animate: {
    x: [-5, 5, -5, 5, 0],
    transition: {
      duration: 0.5,
      ease: "easeOut",
    },
  },
}

export const ripple: Variants = {
  initial: { scale: 0, opacity: 1 },
  animate: {
    scale: 4,
    opacity: 0,
    transition: {
      duration: 0.6,
      ease: "easeOut",
    },
  },
}

// Transition Presets
export const defaultTransition = {
  duration: 0.3,
  ease: "easeInOut",
}

export const smoothTransition = {
  duration: 0.5,
  ease: [0.4, 0, 0.2, 1],
}

export const springTransition = {
  type: "spring",
  stiffness: 300,
  damping: 30,
}

