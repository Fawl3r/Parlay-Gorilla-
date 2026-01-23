"use client"

import { useEffect, useState, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { api } from "@/lib/api"

interface FeedEvent {
  id: string
  event_type: string
  sport: string | null
  summary: string
  created_at: string
  metadata: Record<string, any>
}

export function LiveMarquee() {
  const [events, setEvents] = useState<FeedEvent[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPaused, setIsPaused] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const data = await api.getMarqueeFeed(50)
        setEvents(data)
        if (data.length > 0) {
          setCurrentIndex(0)
        }
      } catch (error) {
        console.error("Error fetching marquee feed:", error)
      }
    }

    fetchEvents()
    const pollInterval = setInterval(fetchEvents, 10000) // Refresh every 10 seconds

    return () => {
      clearInterval(pollInterval)
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (events.length === 0 || isPaused) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    intervalRef.current = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % events.length)
    }, 5000) // Rotate every 5 seconds

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [events.length, isPaused])

  if (events.length === 0) {
    return null
  }

  const currentEvent = events[currentIndex]

  return (
    <div
      className="relative overflow-hidden bg-black/40 border-b border-white/10 py-2"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="container mx-auto px-4">
        <div className="flex items-center gap-4">
          <div className="flex-shrink-0">
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Live Feed</span>
          </div>
          <div className="flex-1 min-w-0">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentEvent.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="text-sm text-white truncate"
              >
                {currentEvent.summary}
              </motion.div>
            </AnimatePresence>
          </div>
          <div className="flex-shrink-0 flex items-center gap-2">
            <div className="flex gap-1">
              {events.map((_, idx) => (
                <div
                  key={idx}
                  className={`h-1 w-1 rounded-full ${
                    idx === currentIndex ? "bg-emerald-400" : "bg-white/20"
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
