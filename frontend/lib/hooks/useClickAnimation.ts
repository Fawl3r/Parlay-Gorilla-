import { useState, useCallback } from "react"
import { useMotionValue, useSpring } from "framer-motion"

export function useClickAnimation() {
  const [isPressed, setIsPressed] = useState(false)
  const scale = useMotionValue(1)
  const scaleSpring = useSpring(scale, { damping: 15, stiffness: 400 })

  const handleMouseDown = useCallback(() => {
    setIsPressed(true)
    scale.set(0.95)
  }, [scale])

  const handleMouseUp = useCallback(() => {
    setIsPressed(false)
    scale.set(1)
  }, [scale])

  const handleMouseLeave = useCallback(() => {
    setIsPressed(false)
    scale.set(1)
  }, [scale])

  return {
    isPressed,
    scale: scaleSpring,
    handleMouseDown,
    handleMouseUp,
    handleMouseLeave,
  }
}
