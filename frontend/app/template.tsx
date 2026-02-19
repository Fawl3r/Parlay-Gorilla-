"use client"

import { motion, AnimatePresence, Variants } from "framer-motion"
import { usePathname } from "next/navigation"
import { ReactNode } from "react"

const pageTransitionVariants: Variants = {
  initial: {
    opacity: 0,
    y: 8,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.3,
      ease: [0.22, 1, 0.36, 1] as [number, number, number, number], // Custom cubic bezier easing
    },
  },
  exit: {
    opacity: 0,
    y: -8,
    transition: {
      duration: 0.2,
      ease: "easeInOut",
    },
  },
}

export default function Template({ children }: { children: ReactNode }) {
  const pathname = usePathname()

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={pathname}
        initial="initial"
        animate="animate"
        exit="exit"
        variants={pageTransitionVariants}
        className="relative min-h-screen"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}

