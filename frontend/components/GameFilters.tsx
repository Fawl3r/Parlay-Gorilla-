"use client"

import React, { useState, useMemo, useEffect } from "react"
import { GameResponse } from "@/lib/api"
import { motion } from "framer-motion"
import { ChevronDown, X } from "lucide-react"
import { cn } from "@/lib/utils"

interface GameFiltersProps {
  games: GameResponse[]
  onFilterChange: (filteredGames: GameResponse[]) => void
  onSportsbookChange?: (sportsbook: string) => void
}

export function GameFilters({ games, onFilterChange, onSportsbookChange }: GameFiltersProps) {
  const [selectedSport, setSelectedSport] = useState<string>("all")
  const [selectedSportsbook, setSelectedSportsbook] = useState<string>("all")
  const [isSportOpen, setIsSportOpen] = useState(false)
  const [isSportsbookOpen, setIsSportsbookOpen] = useState(false)

  // Extract unique sports and sportsbooks
  const { sports, sportsbooks } = useMemo(() => {
    const uniqueSports = new Set<string>()
    const uniqueSportsbooks = new Set<string>()

    games.forEach((game) => {
      if (game.sport) {
        uniqueSports.add(game.sport.toUpperCase())
      }
      game.markets.forEach((market) => {
        if (market.book) {
          uniqueSportsbooks.add(market.book)
        }
      })
    })

    return {
      sports: Array.from(uniqueSports).sort(),
      sportsbooks: Array.from(uniqueSportsbooks).sort(),
    }
  }, [games])

  // Filter games based on selections
  const filteredGames = useMemo(() => {
    return games.filter((game) => {
      // Sport filter
      const sportMatch =
        selectedSport === "all" || game.sport?.toUpperCase() === selectedSport

      // Sportsbook filter - check if game has markets from selected sportsbook
      const sportsbookMatch =
        selectedSportsbook === "all" ||
        game.markets.some((market) => market.book === selectedSportsbook)

      return sportMatch && sportsbookMatch
    })
  }, [games, selectedSport, selectedSportsbook])

  // Update parent when filters change
  useEffect(() => {
    onFilterChange(filteredGames)
  }, [filteredGames, onFilterChange])

  const formatSportsbookName = (book: string): string => {
    return book
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ")
  }

  return (
    <div className="mb-6 flex flex-wrap gap-4">
      {/* Sport Filter */}
      <div className="relative">
        <label className="mb-2 block text-sm font-medium text-muted-foreground">
          Sport
        </label>
        <div className="relative">
          <button
            onClick={() => {
              setIsSportOpen(!isSportOpen)
              setIsSportsbookOpen(false)
            }}
            className={cn(
              "flex w-40 items-center justify-between rounded-lg border bg-card px-4 py-2 text-sm transition-all",
              "hover:border-primary focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
              selectedSport !== "all" && "border-primary"
            )}
            style={{
              borderColor:
                selectedSport !== "all"
                  ? "hsl(var(--primary) / 0.4)"
                  : undefined,
              boxShadow:
                selectedSport !== "all"
                  ? "0 4px 12px hsl(var(--primary) / 0.15)"
                  : undefined,
            }}
          >
            <span className="capitalize">
              {selectedSport === "all" ? "All Sports" : selectedSport}
            </span>
            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform",
                isSportOpen && "rotate-180"
              )}
            />
          </button>

          {isSportOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setIsSportOpen(false)}
              />
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute top-full z-20 mt-2 w-40 rounded-xl border-2 bg-card shadow-xl backdrop-blur-sm"
                style={{
                  borderColor: "hsl(var(--primary) / 0.2)",
                  boxShadow: "0 8px 24px rgba(0, 0, 0, 0.12), 0 4px 12px hsl(var(--primary) / 0.1)",
                }}
              >
                <div className="max-h-60 overflow-y-auto p-1">
                  <button
                    onClick={() => {
                      setSelectedSport("all")
                      setIsSportOpen(false)
                    }}
                    className={cn(
                      "w-full rounded-md px-3 py-2 text-left text-sm transition-colors",
                      selectedSport === "all"
                        ? "bg-primary/20 text-primary"
                        : "hover:bg-muted"
                    )}
                  >
                    All Sports
                  </button>
                  {sports.map((sport) => (
                    <button
                      key={sport}
                      onClick={() => {
                        setSelectedSport(sport)
                        setIsSportOpen(false)
                      }}
                      className={cn(
                        "w-full rounded-md px-3 py-2 text-left text-sm transition-colors",
                        selectedSport === sport
                          ? "bg-primary/20 text-primary"
                          : "hover:bg-muted"
                      )}
                    >
                      {sport}
                    </button>
                  ))}
                </div>
              </motion.div>
            </>
          )}
        </div>
      </div>

      {/* Sportsbook Filter */}
      <div className="relative">
        <label className="mb-2 block text-sm font-medium text-muted-foreground">
          Sportsbook
        </label>
        <div className="relative">
          <button
            onClick={() => {
              setIsSportsbookOpen(!isSportsbookOpen)
              setIsSportOpen(false)
            }}
            className={cn(
              "flex w-48 items-center justify-between rounded-lg border bg-card px-4 py-2 text-sm transition-all",
              "hover:border-primary focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
              selectedSportsbook !== "all" && "border-primary"
            )}
            style={{
              borderColor:
                selectedSportsbook !== "all"
                  ? "hsl(var(--primary) / 0.4)"
                  : undefined,
              boxShadow:
                selectedSportsbook !== "all"
                  ? "0 4px 12px hsl(var(--primary) / 0.15)"
                  : undefined,
            }}
          >
            <span>
              {selectedSportsbook === "all"
                ? "All Sportsbooks"
                : formatSportsbookName(selectedSportsbook)}
            </span>
            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform",
                isSportsbookOpen && "rotate-180"
              )}
            />
          </button>

          {isSportsbookOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setIsSportsbookOpen(false)}
              />
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute top-full z-20 mt-2 w-48 rounded-xl border-2 bg-card shadow-xl backdrop-blur-sm"
                style={{
                  borderColor: "hsl(var(--primary) / 0.2)",
                  boxShadow: "0 8px 24px rgba(0, 0, 0, 0.12), 0 4px 12px hsl(var(--primary) / 0.1)",
                }}
              >
                <div className="max-h-60 overflow-y-auto p-1">
                  <button
                    onClick={() => {
                      setSelectedSportsbook("all")
                      setIsSportsbookOpen(false)
                      onSportsbookChange?.("all")
                    }}
                    className={cn(
                      "w-full rounded-md px-3 py-2 text-left text-sm transition-colors",
                      selectedSportsbook === "all"
                        ? "bg-primary/20 text-primary"
                        : "hover:bg-muted"
                    )}
                  >
                    All Sportsbooks
                  </button>
                  {sportsbooks.map((book) => (
                    <button
                      key={book}
                      onClick={() => {
                        setSelectedSportsbook(book)
                        setIsSportsbookOpen(false)
                        onSportsbookChange?.(book)
                      }}
                      className={cn(
                        "w-full rounded-md px-3 py-2 text-left text-sm transition-colors",
                        selectedSportsbook === book
                          ? "bg-primary/20 text-primary"
                          : "hover:bg-muted"
                      )}
                    >
                      {formatSportsbookName(book)}
                    </button>
                  ))}
                </div>
              </motion.div>
            </>
          )}
        </div>
      </div>

      {/* Active Filters Display */}
      {(selectedSport !== "all" || selectedSportsbook !== "all") && (
        <div className="flex items-end gap-2">
          <div className="flex flex-wrap gap-2">
            {selectedSport !== "all" && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="flex items-center gap-1 rounded-full border px-3 py-1 text-xs"
                style={{
                  borderColor: "hsl(150 100% 50% / 0.5)",
                  backgroundColor: "hsl(150 100% 50% / 0.1)",
                  color: "hsl(150 100% 50%)",
                }}
              >
                <span>{selectedSport}</span>
                <button
                  onClick={() => setSelectedSport("all")}
                  className="ml-1 hover:opacity-70"
                >
                  <X className="h-3 w-3" />
                </button>
              </motion.div>
            )}
            {selectedSportsbook !== "all" && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="flex items-center gap-1 rounded-full border px-3 py-1 text-xs"
                style={{
                  borderColor: "hsl(150 100% 50% / 0.5)",
                  backgroundColor: "hsl(150 100% 50% / 0.1)",
                  color: "hsl(150 100% 50%)",
                }}
              >
                <span>{formatSportsbookName(selectedSportsbook)}</span>
                <button
                  onClick={() => {
                    setSelectedSportsbook("all")
                    onSportsbookChange?.("all")
                  }}
                  className="ml-1 hover:opacity-70"
                >
                  <X className="h-3 w-3" />
                </button>
              </motion.div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

