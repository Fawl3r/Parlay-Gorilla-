"use client"

import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface TeamLogoProps {
  teamName: string
  size?: "sm" | "md" | "lg"
  className?: string
}

// Team color mappings (common team colors)
const teamColors: Record<string, { primary: string; secondary: string }> = {
  // NFL Teams
  "49ers": { primary: "#AA0000", secondary: "#B3995D" },
  "bears": { primary: "#0B162A", secondary: "#C83803" },
  "bengals": { primary: "#FB4F14", secondary: "#000000" },
  "bills": { primary: "#00338D", secondary: "#C60C30" },
  "broncos": { primary: "#FB4F14", secondary: "#002244" },
  "browns": { primary: "#311D00", secondary: "#FF3C00" },
  "buccaneers": { primary: "#D50A0A", secondary: "#FF7900" },
  "cardinals": { primary: "#97233F", secondary: "#000000" },
  "chargers": { primary: "#0080C6", secondary: "#FFC20E" },
  "chiefs": { primary: "#E31837", secondary: "#FFB81C" },
  "colts": { primary: "#002C5F", secondary: "#A2AAAD" },
  "cowboys": { primary: "#003594", secondary: "#869397" },
  "dolphins": { primary: "#008E97", secondary: "#FC4C02" },
  "eagles": { primary: "#004C54", secondary: "#A5ACAF" },
  "falcons": { primary: "#A71930", secondary: "#000000" },
  "giants": { primary: "#0B2265", secondary: "#A71930" },
  "jaguars": { primary: "#006778", secondary: "#9F792C" },
  "jets": { primary: "#125740", secondary: "#000000" },
  "lions": { primary: "#0076B6", secondary: "#B0B7BC" },
  "packers": { primary: "#203731", secondary: "#FFB612" },
  "panthers": { primary: "#0085CA", secondary: "#101820" },
  "patriots": { primary: "#002244", secondary: "#C60C30" },
  "raiders": { primary: "#000000", secondary: "#A5ACAF" },
  "rams": { primary: "#003594", secondary: "#FFA300" },
  "ravens": { primary: "#241773", secondary: "#000000" },
  "saints": { primary: "#D3BC8D", secondary: "#101820" },
  "seahawks": { primary: "#002244", secondary: "#69BE28" },
  "steelers": { primary: "#000000", secondary: "#FFB612" },
  "texans": { primary: "#03202F", secondary: "#A71930" },
  "titans": { primary: "#0C2340", secondary: "#4B92DB" },
  "vikings": { primary: "#4F2683", secondary: "#FFC62F" },
  "washington": { primary: "#5A1414", secondary: "#FFB612" },
  "commanders": { primary: "#5A1414", secondary: "#FFB612" },
  
  // NBA Teams
  "lakers": { primary: "#552583", secondary: "#FDB927" },
  "warriors": { primary: "#1D428A", secondary: "#FFC72C" },
  "celtics": { primary: "#007A33", secondary: "#BA9653" },
  "heat": { primary: "#98002E", secondary: "#F9A01B" },
  "bulls": { primary: "#CE1141", secondary: "#000000" },
  "knicks": { primary: "#006BB6", secondary: "#F58426" },
  "nets": { primary: "#000000", secondary: "#FFFFFF" },
  "clippers": { primary: "#C8102E", secondary: "#1D428A" },
  "suns": { primary: "#1D1160", secondary: "#E56020" },
  "mavericks": { primary: "#00538C", secondary: "#002B5C" },
  
  // NHL Teams
  "bruins": { primary: "#FFB81C", secondary: "#000000" },
  "rangers": { primary: "#0038A8", secondary: "#CE1126" },
  "blackhawks": { primary: "#CF0A2C", secondary: "#000000" },
  "red wings": { primary: "#CE1126", secondary: "#FFFFFF" },
  "maple leafs": { primary: "#00205B", secondary: "#FFFFFF" },
  "canadiens": { primary: "#AF1E2D", secondary: "#192168" },
}

// Get team abbreviation from full name
const getTeamAbbr = (teamName: string): string => {
  const name = teamName.toLowerCase().trim()
  
  // Common abbreviations
  const abbreviations: Record<string, string> = {
    "san francisco 49ers": "SF",
    "chicago bears": "CHI",
    "cincinnati bengals": "CIN",
    "buffalo bills": "BUF",
    "denver broncos": "DEN",
    "cleveland browns": "CLE",
    "tampa bay buccaneers": "TB",
    "arizona cardinals": "ARI",
    "los angeles chargers": "LAC",
    "kansas city chiefs": "KC",
    "indianapolis colts": "IND",
    "dallas cowboys": "DAL",
    "miami dolphins": "MIA",
    "philadelphia eagles": "PHI",
    "atlanta falcons": "ATL",
    "new york giants": "NYG",
    "jacksonville jaguars": "JAX",
    "new york jets": "NYJ",
    "detroit lions": "DET",
    "green bay packers": "GB",
    "carolina panthers": "CAR",
    "new england patriots": "NE",
    "las vegas raiders": "LV",
    "oakland raiders": "OAK",
    "los angeles rams": "LAR",
    "baltimore ravens": "BAL",
    "new orleans saints": "NO",
    "seattle seahawks": "SEA",
    "pittsburgh steelers": "PIT",
    "houston texans": "HOU",
    "tennessee titans": "TEN",
    "minnesota vikings": "MIN",
    "washington commanders": "WAS",
    "washington football team": "WAS",
    "washington": "WAS",
  }
  
  // Try exact match first
  if (abbreviations[name]) {
    return abbreviations[name]
  }
  
  // Try partial match
  for (const [key, abbr] of Object.entries(abbreviations)) {
    if (name.includes(key) || key.includes(name)) {
      return abbr
    }
  }
  
  // Fallback: use first letters of words
  const words = name.split(" ")
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  
  // Single word: use first 2-3 letters
  return name.substring(0, Math.min(3, name.length)).toUpperCase()
}

// Get team colors
const getTeamColors = (teamName: string): { primary: string; secondary: string } => {
  const name = teamName.toLowerCase().trim()
  
  // Try exact match
  for (const [key, colors] of Object.entries(teamColors)) {
    if (name.includes(key) || key.includes(name)) {
      return colors
    }
  }
  
  // Default colors
  return { primary: "#1E293B", secondary: "#38BDF8" }
}

const sizeMap = {
  sm: "h-8 w-8 text-xs",
  md: "h-12 w-12 text-sm",
  lg: "h-16 w-16 text-base",
}

export function TeamLogo({ teamName, size = "md", className }: TeamLogoProps) {
  const abbr = getTeamAbbr(teamName)
  const colors = getTeamColors(teamName)
  
  return (
    <motion.div
      className={cn(
        "relative flex items-center justify-center rounded-full font-bold text-white",
        sizeMap[size],
        className
      )}
      style={{
        background: `linear-gradient(135deg, ${colors.primary}, ${colors.secondary})`,
        boxShadow: `0 0 20px ${colors.primary}80, inset 0 0 20px ${colors.secondary}40`,
      }}
      whileHover={{ scale: 1.1, rotate: 5 }}
      transition={{ duration: 0.2 }}
    >
      <span className="relative z-10 drop-shadow-lg">{abbr}</span>
      
      {/* Glow effect */}
      <motion.div
        className="absolute inset-0 rounded-full opacity-0 blur-xl"
        style={{ backgroundColor: colors.primary }}
        whileHover={{ opacity: 0.6 }}
        transition={{ duration: 0.3 }}
      />
    </motion.div>
  )
}

