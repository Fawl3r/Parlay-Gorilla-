import { useState, useCallback } from "react"
import { useMotionValue, useSpring, useTransform } from "framer-motion"

export function useHoverAnimation() {
  const [isHovered, setIsHovered] = useState(false)
  const x = useMotionValue(0)
  const y = useMotionValue(0)

  const springConfig = { damping: 25, stiffness: 700 }
  const xSpring = useSpring(x, springConfig)
  const ySpring = useSpring(y, springConfig)

  const rotateX = useTransform(ySpring, [-0.5, 0.5], ["17.5deg", "-17.5deg"])
  const rotateY = useTransform(xSpring, [-0.5, 0.5], ["-17.5deg", "17.5deg"])

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLElement>) => {
      if (!isHovered) return

      const rect = e.currentTarget.getBoundingClientRect()
      const width = rect.width
      const height = rect.height
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top
      const xPct = mouseX / width - 0.5
      const yPct = mouseY / height - 0.5

      x.set(xPct)
      y.set(yPct)
    },
    [isHovered, x, y]
  )

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true)
  }, [])

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false)
    x.set(0)
    y.set(0)
  }, [x, y])

  return {
    isHovered,
    handleMouseMove,
    handleMouseEnter,
    handleMouseLeave,
    rotateX,
    rotateY,
  }
}
