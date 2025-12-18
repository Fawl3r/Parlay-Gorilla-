"use client"

import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { getTeamStyle, type TeamStyle } from "@/lib/constants/teamStyles"

interface TeamBadgeProps {
  teamName: string
  sport?: string // nfl, nba, nhl, mlb, ncaaf, ncaab, soccer
  size?: "sm" | "md" | "lg"
  className?: string
  location?: "Home" | "Away"
  showName?: boolean
}

const sizeMap = {
  sm: "h-8 w-8 text-xs",
  md: "h-12 w-12 text-sm",
  lg: "h-16 w-16 text-base",
}

const sizeMapPill = {
  sm: "h-6 px-2 text-xs",
  md: "h-8 px-3 text-sm",
  lg: "h-10 px-4 text-base",
}

/**
 * TeamBadge Component
 * 
 * Displays team identity using abbreviation and colors ONLY.
 * NO logos, NO images, NO trademarked graphics.
 * 
 * Legal compliance: Team names and abbreviations are used solely for identification purposes.
 */
export function TeamBadge({ 
  teamName, 
  sport, 
  size = "md", 
  className,
  location,
  showName = false,
}: TeamBadgeProps) {
  const teamStyle = getTeamStyle(teamName, sport)
  const { label, primary, secondary, name } = teamStyle
  
  // If showName is true, render as a pill with text
  if (showName) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <motion.div
          className={cn(
            "relative flex items-center justify-center rounded-full font-bold text-white",
            sizeMap[size],
          )}
          style={{
            background: `linear-gradient(135deg, ${primary}, ${secondary})`,
            boxShadow: `0 0 20px ${primary}80, inset 0 0 20px ${secondary}40`,
          }}
          whileHover={{ scale: 1.1, rotate: 5 }}
          transition={{ duration: 0.2 }}
        >
          <span className="relative z-10 drop-shadow-lg">{label}</span>
          
          {/* Glow effect */}
          <motion.div
            className="absolute inset-0 rounded-full opacity-0 blur-xl"
            style={{ backgroundColor: primary }}
            whileHover={{ opacity: 0.6 }}
            transition={{ duration: 0.3 }}
          />
        </motion.div>
        <span className="font-medium text-gray-900 dark:text-white">{name || teamName}</span>
        {location && (
          <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            {location}
          </span>
        )}
      </div>
    )
  }
  
  // Default: circular badge with abbreviation
  return (
    <motion.div
      className={cn(
        "relative flex items-center justify-center rounded-full font-bold text-white",
        sizeMap[size],
        className
      )}
      style={{
        background: `linear-gradient(135deg, ${primary}, ${secondary})`,
        boxShadow: `0 0 20px ${primary}80, inset 0 0 20px ${secondary}40`,
      }}
      whileHover={{ scale: 1.1, rotate: 5 }}
      transition={{ duration: 0.2 }}
    >
      <span className="relative z-10 drop-shadow-lg">{label}</span>
      
      {/* Glow effect */}
      <motion.div
        className="absolute inset-0 rounded-full opacity-0 blur-xl"
        style={{ backgroundColor: primary }}
        whileHover={{ opacity: 0.6 }}
        transition={{ duration: 0.3 }}
      />
      
      {/* Optional location indicator */}
      {location && (
        <div 
          className="absolute -bottom-1 -right-1 rounded-full bg-white dark:bg-gray-800 border-2 border-white dark:border-gray-700"
          style={{ 
            width: size === "sm" ? "12px" : size === "md" ? "16px" : "20px",
            height: size === "sm" ? "12px" : size === "md" ? "16px" : "20px",
          }}
        >
          <span 
            className="absolute inset-0 flex items-center justify-center text-[8px] font-bold"
            style={{ color: location === "Home" ? primary : secondary }}
          >
            {location === "Home" ? "H" : "A"}
          </span>
        </div>
      )}
    </motion.div>
  )
}

/**
 * TeamPill Component
 * 
 * A horizontal pill variant for compact spaces (e.g., parlay builder lists)
 */
export function TeamPill({
  teamName,
  sport,
  size = "md",
  className,
}: Omit<TeamBadgeProps, "location" | "showName">) {
  const teamStyle = getTeamStyle(teamName, sport)
  const { label, primary, secondary } = teamStyle
  
  return (
    <motion.div
      className={cn(
        "inline-flex items-center justify-center rounded-full font-bold text-white",
        sizeMapPill[size],
        className
      )}
      style={{
        background: `linear-gradient(135deg, ${primary}, ${secondary})`,
        boxShadow: `0 0 15px ${primary}60`,
      }}
      whileHover={{ scale: 1.05 }}
      transition={{ duration: 0.2 }}
    >
      <span className="drop-shadow-md">{label}</span>
    </motion.div>
  )
}



