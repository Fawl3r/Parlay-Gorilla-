"use client"

import { Card, CardContent, CardHeader } from "@/components/ui/card"

export function ParlayBuilderSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header Skeleton */}
      <Card className="border-2 border-primary/20 bg-card/50">
        <CardHeader className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="h-8 w-48 rounded bg-gray-700 animate-pulse" />
            <div className="h-6 w-24 rounded bg-gray-700 animate-pulse" />
          </div>
          <div className="h-4 w-64 rounded bg-gray-700 animate-pulse" />
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Legs Slider Skeleton */}
          <div className="space-y-2">
            <div className="h-4 w-24 rounded bg-gray-700 animate-pulse" />
            <div className="h-10 w-full rounded bg-gray-700 animate-pulse" />
          </div>
          
          {/* Risk Profile Skeleton */}
          <div className="space-y-2">
            <div className="h-4 w-24 rounded bg-gray-700 animate-pulse" />
            <div className="flex gap-2">
              <div className="h-10 flex-1 rounded bg-gray-700 animate-pulse" />
              <div className="h-10 flex-1 rounded bg-gray-700 animate-pulse" />
              <div className="h-10 flex-1 rounded bg-gray-700 animate-pulse" />
            </div>
          </div>
          
          {/* Sports Selection Skeleton */}
          <div className="space-y-2">
            <div className="h-4 w-24 rounded bg-gray-700 animate-pulse" />
            <div className="flex gap-2">
              <div className="h-10 w-20 rounded bg-gray-700 animate-pulse" />
              <div className="h-10 w-20 rounded bg-gray-700 animate-pulse" />
              <div className="h-10 w-20 rounded bg-gray-700 animate-pulse" />
              <div className="h-10 w-20 rounded bg-gray-700 animate-pulse" />
            </div>
          </div>
          
          {/* Generate Button Skeleton */}
          <div className="h-12 w-full rounded bg-gradient-to-r from-emerald-600/50 to-green-600/50 animate-pulse" />
        </CardContent>
      </Card>
      
      {/* Result Placeholder */}
      <Card className="border-2 border-dashed border-primary/20 bg-card/30">
        <CardContent className="py-12 flex flex-col items-center justify-center text-center">
          <div className="h-16 w-16 rounded-full bg-gray-700/50 animate-pulse mb-4" />
          <div className="h-5 w-48 rounded bg-gray-700/50 animate-pulse mb-2" />
          <div className="h-4 w-64 rounded bg-gray-700/50 animate-pulse" />
        </CardContent>
      </Card>
    </div>
  )
}

export function ParlayResultSkeleton() {
  return (
    <Card className="border-2 border-primary/30 bg-card/80">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="h-6 w-32 rounded bg-gray-700 animate-pulse" />
          <div className="h-8 w-24 rounded bg-gray-700 animate-pulse" />
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Legs */}
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 p-4 rounded-lg bg-gray-800/50">
            <div className="h-10 w-10 rounded-full bg-gray-700 animate-pulse" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-32 rounded bg-gray-700 animate-pulse" />
              <div className="h-3 w-48 rounded bg-gray-700 animate-pulse" />
            </div>
            <div className="h-6 w-16 rounded bg-gray-700 animate-pulse" />
          </div>
        ))}
        
        {/* AI Summary */}
        <div className="p-4 rounded-lg bg-gray-800/50 space-y-2">
          <div className="h-5 w-24 rounded bg-gray-700 animate-pulse" />
          <div className="h-4 w-full rounded bg-gray-700 animate-pulse" />
          <div className="h-4 w-3/4 rounded bg-gray-700 animate-pulse" />
        </div>
      </CardContent>
    </Card>
  )
}

