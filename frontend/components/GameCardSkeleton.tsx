"use client"

import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface GameCardSkeletonProps {
  className?: string
}

export function GameCardSkeleton({ className }: GameCardSkeletonProps) {
  return (
    <Card className={cn(
      "overflow-hidden border-2 border-primary/20 bg-card/50",
      className
    )}>
      <CardHeader className="pb-4">
        {/* Team Matchup Skeleton */}
        <div className="mb-6 flex items-center justify-center gap-6">
          {/* Away Team */}
          <div className="flex flex-col items-center gap-3">
            <div className="h-16 w-16 rounded-full bg-gradient-to-r from-gray-700 via-gray-600 to-gray-700 animate-pulse" />
            <div className="h-3 w-16 rounded bg-gray-700 animate-pulse" />
          </div>
          
          {/* VS */}
          <div className="flex flex-col items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-gray-700 animate-pulse" />
            <div className="h-1 w-20 bg-gray-700 animate-pulse" />
          </div>
          
          {/* Home Team */}
          <div className="flex flex-col items-center gap-3">
            <div className="h-16 w-16 rounded-full bg-gradient-to-r from-gray-700 via-gray-600 to-gray-700 animate-pulse" />
            <div className="h-3 w-16 rounded bg-gray-700 animate-pulse" />
          </div>
        </div>

        {/* Game Info Skeleton */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <div className="h-4 w-24 rounded bg-gray-700 animate-pulse" />
              <div className="h-5 w-16 rounded bg-gray-700 animate-pulse" />
            </div>
          </div>
          <div className="h-5 w-20 rounded bg-gray-700 animate-pulse" />
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {/* Odds Skeleton */}
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-4">
            <div className="h-4 w-16 rounded bg-gray-700 animate-pulse" />
            <div className="flex gap-2">
              <div className="h-8 w-16 rounded bg-gray-700 animate-pulse" />
              <div className="h-8 w-16 rounded bg-gray-700 animate-pulse" />
            </div>
          </div>
          <div className="flex items-center justify-between gap-4">
            <div className="h-4 w-16 rounded bg-gray-700 animate-pulse" />
            <div className="flex gap-2">
              <div className="h-8 w-16 rounded bg-gray-700 animate-pulse" />
              <div className="h-8 w-16 rounded bg-gray-700 animate-pulse" />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function GameCardSkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <GameCardSkeleton key={i} />
      ))}
    </div>
  )
}

