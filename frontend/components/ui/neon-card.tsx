"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { cardTilt } from "@/lib/animations"

const NeonCard = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    glowColor?: "neon" | "gold" | "sky" | "none"
    tiltOnHover?: boolean
  }
>(({ className, glowColor = "neon", tiltOnHover = true, children, onClick }, ref) => {
  const glowStyles = {
    neon: {
      borderColor: "hsl(var(--primary) / 0.5)",
      boxShadow: "0 0 20px hsl(var(--primary) / 0.3), inset 0 0 20px hsl(var(--primary) / 0.1)",
    },
    gold: {
      borderColor: "hsl(var(--gold) / 0.5)",
      boxShadow: "0 0 20px hsl(var(--gold) / 0.3), inset 0 0 20px hsl(var(--gold) / 0.1)",
    },
    sky: {
      borderColor: "hsl(var(--accent) / 0.5)",
      boxShadow: "0 0 20px hsl(var(--accent) / 0.3), inset 0 0 20px hsl(var(--accent) / 0.1)",
    },
    none: {},
  }

  return (
    <motion.div
      ref={ref}
      className={cn(
        "rounded-lg border bg-card text-card-foreground shadow-sm transition-all",
        className
      )}
      style={glowColor !== "none" ? glowStyles[glowColor] : undefined}
      variants={tiltOnHover ? cardTilt : undefined}
      whileHover={tiltOnHover ? "animate" : undefined}
      transition={{ duration: 0.3, ease: "easeOut" }}
      onClick={onClick}
    >
      {children}
    </motion.div>
  )
})
NeonCard.displayName = "NeonCard"

const NeonCardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
))
NeonCardHeader.displayName = "NeonCardHeader"

const NeonCardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-2xl font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
NeonCardTitle.displayName = "NeonCardTitle"

const NeonCardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
NeonCardDescription.displayName = "NeonCardDescription"

const NeonCardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
NeonCardContent.displayName = "NeonCardContent"

const NeonCardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
))
NeonCardFooter.displayName = "NeonCardFooter"

export {
  NeonCard,
  NeonCardHeader,
  NeonCardFooter,
  NeonCardTitle,
  NeonCardDescription,
  NeonCardContent,
}

