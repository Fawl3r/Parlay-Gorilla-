"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { 
  X, 
  Check, 
  TrendingUp, 
  Sparkles,
  ChevronRight,
  Trophy,
  Zap
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export interface BetSlipLeg {
  id: string
  game: string
  pick: string
  odds: string
  confidence?: number
  is_upset?: boolean
}

interface BetSlipAnimationProps {
  legs: BetSlipLeg[]
  isOpen: boolean
  onClose: () => void
  onRemoveLeg: (legId: string) => void
  onBuildParlay: () => void
  parlayOdds?: string
  hitProbability?: number
  isAIApproved?: boolean
}

export function BetSlipAnimation({
  legs,
  isOpen,
  onClose,
  onRemoveLeg,
  onBuildParlay,
  parlayOdds,
  hitProbability,
  isAIApproved = false
}: BetSlipAnimationProps) {
  const [showStamp, setShowStamp] = useState(false)

  useEffect(() => {
    if (isAIApproved && isOpen) {
      // Show stamp animation after a short delay
      const timer = setTimeout(() => setShowStamp(true), 500)
      return () => clearTimeout(timer)
    } else {
      setShowStamp(false)
    }
  }, [isAIApproved, isOpen])

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          />
          
          {/* Bet Slip Panel */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-gradient-to-b from-gray-900 to-black border-l border-emerald-500/30 z-50 flex flex-col"
          >
            {/* Header */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <motion.div
                  animate={{ 
                    boxShadow: isAIApproved 
                      ? ["0 0 0 0 rgba(16,185,129,0)", "0 0 20px 10px rgba(16,185,129,0.3)", "0 0 0 0 rgba(16,185,129,0)"]
                      : "none"
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center"
                >
                  <Zap className="h-5 w-5 text-emerald-400" />
                </motion.div>
                <div>
                  <h2 className="text-lg font-bold text-white">Bet Slip</h2>
                  <p className="text-xs text-gray-400">{legs.length} leg{legs.length !== 1 ? "s" : ""} selected</p>
                </div>
              </div>
              
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              >
                <X className="h-5 w-5 text-gray-400" />
              </button>
            </div>
            
            {/* Legs List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {legs.length === 0 ? (
                <div className="text-center py-12">
                  <TrendingUp className="h-10 w-10 text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-400 text-sm">No legs added yet</p>
                  <p className="text-gray-500 text-xs mt-1">Click on odds to add legs</p>
                </div>
              ) : (
                <AnimatePresence mode="popLayout">
                  {legs.map((leg, index) => (
                    <motion.div
                      key={leg.id}
                      layout
                      initial={{ opacity: 0, x: 50, scale: 0.8 }}
                      animate={{ opacity: 1, x: 0, scale: 1 }}
                      exit={{ opacity: 0, x: -50, scale: 0.8 }}
                      transition={{ 
                        type: "spring", 
                        damping: 20, 
                        stiffness: 300,
                        delay: index * 0.05 
                      }}
                      className="relative p-3 rounded-xl bg-white/[0.03] border border-white/10 group"
                    >
                      {/* Remove Button */}
                      <button
                        onClick={() => onRemoveLeg(leg.id)}
                        className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-red-500 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <X className="h-3 w-3 text-white" />
                      </button>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-white text-sm truncate">
                              {leg.pick}
                            </span>
                            {leg.is_upset && (
                              <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30 text-xs px-1.5">
                                🦍
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-gray-500 truncate mt-0.5">{leg.game}</p>
                        </div>
                        
                        <div className="text-right ml-3">
                          <div className="font-bold text-emerald-400 text-sm">{leg.odds}</div>
                          {leg.confidence && (
                            <div className="text-xs text-gray-500">{leg.confidence.toFixed(0)}% conf</div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              )}
            </div>
            
            {/* Summary & Actions */}
            {legs.length > 0 && (
              <div className="p-4 border-t border-white/10 bg-black/50 relative overflow-hidden">
                {/* AI Approved Stamp Animation */}
                <AnimatePresence>
                  {showStamp && isAIApproved && (
                    <motion.div
                      initial={{ scale: 3, opacity: 0, rotate: -30 }}
                      animate={{ scale: 1, opacity: 1, rotate: -15 }}
                      exit={{ scale: 0.5, opacity: 0 }}
                      transition={{ type: "spring", damping: 10, stiffness: 100 }}
                      className="absolute top-4 right-4 z-10"
                    >
                      <div className="relative">
                        {/* Glow Effect */}
                        <motion.div
                          animate={{ 
                            boxShadow: [
                              "0 0 20px 10px rgba(16,185,129,0.3)",
                              "0 0 40px 20px rgba(16,185,129,0.5)",
                              "0 0 20px 10px rgba(16,185,129,0.3)"
                            ]
                          }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                          className="absolute inset-0 rounded-xl"
                        />
                        
                        {/* Stamp */}
                        <div className="relative px-4 py-2 rounded-xl border-4 border-emerald-500 bg-emerald-500/20 backdrop-blur-sm">
                          <div className="flex items-center gap-2">
                            <Trophy className="h-5 w-5 text-emerald-400" />
                            <div>
                              <div className="text-xs text-emerald-300 font-bold uppercase tracking-wider">
                                AI Approved
                              </div>
                              <div className="text-emerald-400 text-[10px]">🦍 Gorilla Pick</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
                
                {/* Parlay Stats */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  {parlayOdds && (
                    <div className="p-3 rounded-lg bg-white/[0.03]">
                      <div className="text-xs text-gray-500 mb-1">Parlay Odds</div>
                      <div className="text-xl font-black text-emerald-400">{parlayOdds}</div>
                    </div>
                  )}
                  
                  {hitProbability !== undefined && (
                    <div className="p-3 rounded-lg bg-white/[0.03]">
                      <div className="text-xs text-gray-500 mb-1">Hit Probability</div>
                      <div className="text-xl font-black text-white">{(hitProbability * 100).toFixed(1)}%</div>
                    </div>
                  )}
                </div>
                
                {/* Build Button */}
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Button
                    onClick={onBuildParlay}
                    className="w-full bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400 text-black font-bold py-6 text-lg relative overflow-hidden group"
                  >
                    {/* Shimmer Effect */}
                    <motion.div
                      className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                      animate={{ x: ["-200%", "200%"] }}
                      transition={{ duration: 2, repeat: Infinity, repeatDelay: 1 }}
                    />
                    
                    <span className="relative flex items-center gap-2">
                      <Sparkles className="h-5 w-5" />
                      Build Parlay
                      <ChevronRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                    </span>
                  </Button>
                </motion.div>
                
                <p className="text-xs text-gray-500 text-center mt-3">
                  For entertainment purposes only. Please bet responsibly.
                </p>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

// Compact floating bet slip button for use across the app
interface FloatingBetSlipButtonProps {
  legCount: number
  onClick: () => void
}

export function FloatingBetSlipButton({ legCount, onClick }: FloatingBetSlipButtonProps) {
  if (legCount === 0) return null
  
  return (
    <motion.button
      initial={{ opacity: 0, y: 100, scale: 0.8 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 100, scale: 0.8 }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className="fixed bottom-6 right-6 z-40"
    >
      <div className="relative">
        {/* Pulse Effect */}
        <motion.div
          animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute inset-0 bg-emerald-500 rounded-full"
        />
        
        {/* Button */}
        <div className="relative flex items-center gap-3 px-5 py-3 rounded-full bg-emerald-500 text-black shadow-lg shadow-emerald-500/30">
          <motion.div
            animate={{ rotate: [0, 10, -10, 0] }}
            transition={{ duration: 0.5, repeat: Infinity, repeatDelay: 3 }}
            className="w-7 h-7 rounded-full bg-black/20 flex items-center justify-center text-sm font-bold"
          >
            {legCount}
          </motion.div>
          <span className="font-semibold">Bet Slip</span>
          <TrendingUp className="h-5 w-5" />
        </div>
      </div>
    </motion.button>
  )
}

// Mini bet slip preview (shows in corner without opening full panel)
interface MiniBetSlipProps {
  legs: BetSlipLeg[]
  parlayOdds?: string
  onExpand: () => void
  onClear: () => void
}

export function MiniBetSlip({ legs, parlayOdds, onExpand, onClear }: MiniBetSlipProps) {
  if (legs.length === 0) return null
  
  return (
    <motion.div
      initial={{ opacity: 0, x: 100 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 100 }}
      className="fixed bottom-6 right-6 z-40 w-72"
    >
      <div className="bg-gray-900/95 backdrop-blur-lg border border-emerald-500/30 rounded-2xl overflow-hidden shadow-xl shadow-emerald-500/10">
        {/* Header */}
        <div className="p-3 bg-emerald-500/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-emerald-400" />
            <span className="text-sm font-bold text-white">Bet Slip</span>
            <Badge className="bg-emerald-500 text-black text-xs">{legs.length}</Badge>
          </div>
          <button
            onClick={onClear}
            className="text-xs text-gray-400 hover:text-red-400 transition-colors"
          >
            Clear
          </button>
        </div>
        
        {/* Preview Legs */}
        <div className="p-3 space-y-1.5 max-h-32 overflow-y-auto">
          {legs.slice(0, 3).map((leg) => (
            <div key={leg.id} className="flex items-center justify-between text-xs">
              <span className="text-gray-300 truncate flex-1">{leg.pick}</span>
              <span className="text-emerald-400 ml-2">{leg.odds}</span>
            </div>
          ))}
          {legs.length > 3 && (
            <div className="text-xs text-gray-500 text-center">
              +{legs.length - 3} more
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-3 border-t border-white/10 flex items-center justify-between">
          {parlayOdds && (
            <div className="text-sm">
              <span className="text-gray-400">Odds: </span>
              <span className="font-bold text-emerald-400">{parlayOdds}</span>
            </div>
          )}
          <Button
            size="sm"
            onClick={onExpand}
            className="bg-emerald-500 hover:bg-emerald-600 text-black text-xs"
          >
            View Slip
          </Button>
        </div>
      </div>
    </motion.div>
  )
}




