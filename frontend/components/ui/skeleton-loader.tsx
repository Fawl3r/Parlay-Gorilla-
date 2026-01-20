"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

export interface SkeletonLoaderProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "card" | "text" | "circular"
  lines?: number
}

export function SkeletonLoader({
  className,
  variant = "default",
  lines = 1,
  ...props
}: SkeletonLoaderProps) {
  if (variant === "card") {
    return (
      <div
        className={cn(
          "rounded-xl border border-white/8 bg-[rgba(18,18,23,0.6)] backdrop-blur-md p-6",
          className
        )}
        {...props}
      >
        <SkeletonShimmer>
          <div className="space-y-4">
            <div className="h-4 w-3/4 bg-white/10 rounded" />
            <div className="h-4 w-1/2 bg-white/10 rounded" />
            <div className="h-32 w-full bg-white/10 rounded" />
          </div>
        </SkeletonShimmer>
      </div>
    )
  }

  if (variant === "text") {
    return (
      <div className={cn("space-y-2", className)} {...props}>
        {Array.from({ length: lines }).map((_, i) => (
          <SkeletonShimmer key={i}>
            <div
              className={cn(
                "h-4 bg-white/10 rounded",
                i === lines - 1 && "w-3/4"
              )}
            />
          </SkeletonShimmer>
        ))}
      </div>
    )
  }

  if (variant === "circular") {
    return (
      <SkeletonShimmer>
        <div className={cn("rounded-full bg-white/10", className)} {...props} />
      </SkeletonShimmer>
    )
  }

  return (
    <SkeletonShimmer>
      <div className={cn("h-4 w-full bg-white/10 rounded", className)} {...props} />
    </SkeletonShimmer>
  )
}

function SkeletonShimmer({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative overflow-hidden">
      {children}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
        animate={{
          x: ["-100%", "100%"],
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: "linear",
        }}
      />
    </div>
  )
}
