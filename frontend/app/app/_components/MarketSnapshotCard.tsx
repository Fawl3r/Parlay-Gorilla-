"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { BarChart3 } from "lucide-react"
import { getMarketSnapshotEntries, type MarketSnapshotEntry } from "@/lib/retention"

function getHighestConfidence(entries: MarketSnapshotEntry[]): MarketSnapshotEntry | null {
  if (entries.length === 0) return null
  return entries.reduce((best, e) => (e.confidence > best.confidence ? e : best))
}

function getMostBalanced(entries: MarketSnapshotEntry[]): MarketSnapshotEntry | null {
  if (entries.length === 0) return null
  return entries.reduce((best, e) => {
    const dev = Math.abs(e.confidence - 50)
    const bestDev = Math.abs(best.confidence - 50)
    return dev < bestDev ? e : best
  })
}

function getLargestEdge(entries: MarketSnapshotEntry[]): MarketSnapshotEntry | null {
  if (entries.length === 0) return null
  const withEdge = entries.filter((e) => e.edgeLabel)
  if (withEdge.length > 0) {
    return withEdge.reduce((best, e) => (e.confidence > best.confidence ? e : best))
  }
  return getHighestConfidence(entries)
}

export function MarketSnapshotCard() {
  const [entries, setEntries] = useState<MarketSnapshotEntry[]>([])

  useEffect(() => {
    setEntries(getMarketSnapshotEntries())
  }, [])

  if (entries.length === 0) return null

  const highest = getHighestConfidence(entries)
  const balanced = getMostBalanced(entries)
  const edge = getLargestEdge(entries)

  return (
    <div className="rounded-xl border border-white/10 bg-black/30 backdrop-blur-sm p-4 mb-3">
      <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
        <BarChart3 className="h-4 w-4 text-emerald-400/80" />
        Market Snapshot
      </h3>
      <ul className="text-xs text-white/95 space-y-2">
        {highest && (
          <li>
            <span className="text-white/65">Highest confidence: </span>
            <Link href={`/analysis/${highest.slug}`} className="text-emerald-400/90 hover:underline">
              {highest.matchup}
            </Link>
            <span className="text-white/92"> ({Math.round(highest.confidence)}%)</span>
          </li>
        )}
        {balanced && balanced !== highest && (
          <li>
            <span className="text-white/65">Most balanced: </span>
            <Link href={`/analysis/${balanced.slug}`} className="text-emerald-400/90 hover:underline">
              {balanced.matchup}
            </Link>
            <span className="text-white/92"> ({Math.round(balanced.confidence)}%)</span>
          </li>
        )}
        {edge && edge !== highest && (
          <li>
            <span className="text-white/65">Largest edge: </span>
            <Link href={`/analysis/${edge.slug}`} className="text-emerald-400/90 hover:underline">
              {edge.matchup}
            </Link>
            {edge.edgeLabel && (
              <span className="text-white/92"> — {edge.edgeLabel}</span>
            )}
          </li>
        )}
      </ul>
    </div>
  )
}
