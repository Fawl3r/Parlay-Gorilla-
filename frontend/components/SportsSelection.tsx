"use client"

import { motion } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { staggerContainer, staggerItem } from "@/lib/animations"
import { 
  Football, 
  Basketball, 
  Baseball, 
  Hockey, 
  Soccer, 
  Activity,
  Target 
} from "lucide-react"

interface Sport {
  id: string
  name: string
  icon: React.ComponentType<{ className?: string }>
  color: string
  gradient: string
  description: string
}

const sports: Sport[] = [
  {
    id: "nfl",
    name: "NFL",
    icon: Football,
    color: "hsl(0 84% 60%)",
    gradient: "from-red-500/20 to-orange-500/20",
    description: "American Football",
  },
  {
    id: "nba",
    name: "NBA",
    icon: Basketball,
    color: "hsl(25 95% 53%)",
    gradient: "from-orange-500/20 to-amber-500/20",
    description: "Basketball",
  },
  {
    id: "mlb",
    name: "MLB",
    icon: Baseball,
    color: "hsl(48 96% 53%)",
    gradient: "from-blue-500/20 to-cyan-500/20",
    description: "Baseball",
  },
  {
    id: "nhl",
    name: "NHL",
    icon: Hockey,
    color: "hsl(199 89% 48%)",
    gradient: "from-blue-500/20 to-indigo-500/20",
    description: "Hockey",
  },
  {
    id: "soccer",
    name: "Soccer",
    icon: Soccer,
    color: "hsl(142 76% 36%)",
    gradient: "from-green-500/20 to-emerald-500/20",
    description: "Football",
  },
  {
    id: "ufc",
    name: "UFC",
    icon: Activity,
    color: "hsl(0 84% 60%)",
    gradient: "from-red-500/20 to-rose-500/20",
    description: "Mixed Martial Arts",
  },
  {
    id: "boxing",
    name: "Boxing",
    icon: Target,
    color: "hsl(25 95% 53%)",
    gradient: "from-amber-500/20 to-yellow-500/20",
    description: "Boxing",
  },
]

interface SportsSelectionProps {
  onSportSelect?: (sportId: string) => void
  selectedSports?: string[]
}

export function SportsSelection({ 
  onSportSelect, 
  selectedSports = [] 
}: SportsSelectionProps) {
  return (
    <section className="relative py-20 md:py-32">
      {/* Dark Overlay */}
      <div className="absolute inset-0 dark-overlay-strong z-0" />
      
      <div className="container relative z-10 px-4">
        <motion.div
          className="mb-12 text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="mb-4 text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
            <span className="gradient-text">Pick Your Sport</span>
          </h2>
          <p className="text-lg text-foreground/80 max-w-2xl mx-auto">
            Select one or more sports to build your parlay
          </p>
        </motion.div>

        <motion.div
          className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
          variants={staggerContainer}
          initial="initial"
          animate="animate"
        >
          {sports.map((sport) => {
            const isSelected = selectedSports.includes(sport.id)
            const Icon = sport.icon

            return (
              <motion.div
                key={sport.id}
                variants={staggerItem}
                whileHover={{ scale: 1.05, y: -5 }}
                whileTap={{ scale: 0.95 }}
              >
                <Card
                  className={`group relative overflow-hidden border-2 transition-all duration-300 cursor-pointer h-full ${
                    isSelected
                      ? "border-primary shadow-lg shadow-primary/50"
                      : "border-primary/30 hover:border-primary/60"
                  } card-elevated hover:card-elevated-hover neon-glow-effect`}
                  onClick={() => onSportSelect?.(sport.id)}
                >
                  {/* Gorilla-themed visual variation */}
                  <div
                    className={`absolute inset-0 bg-gradient-to-br ${sport.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`}
                  />
                  <div className="absolute inset-0 circuit-pattern opacity-0 group-hover:opacity-20 transition-opacity" />
                  
                  {/* Selection indicator */}
                  {isSelected && (
                    <motion.div
                      className="absolute top-2 right-2 w-6 h-6 rounded-full bg-primary flex items-center justify-center"
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 500 }}
                    >
                      <motion.div
                        className="w-3 h-3 rounded-full bg-primary-foreground"
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 1, repeat: Infinity }}
                      />
                    </motion.div>
                  )}

                  <CardContent className="relative p-8 flex flex-col items-center text-center">
                    <motion.div
                      className={`mb-4 flex h-20 w-20 items-center justify-center rounded-2xl ${
                        isSelected
                          ? "bg-gradient-to-br from-primary/40 to-secondary/40"
                          : "bg-gradient-to-br from-primary/20 to-secondary/20"
                      } group-hover:from-primary/50 group-hover:to-secondary/50 transition-all duration-300 team-badge`}
                      whileHover={{ rotate: [0, -10, 10, -10, 0] }}
                      transition={{ duration: 0.5 }}
                    >
                      <Icon
                        className="h-10 w-10"
                        style={{
                          color: isSelected ? "hsl(150 100% 50%)" : sport.color,
                        }}
                      />
                    </motion.div>

                    <h3 className="mb-2 text-2xl font-bold text-foreground">
                      {sport.name}
                    </h3>
                    <p className="text-sm text-foreground/70">
                      {sport.description}
                    </p>

                    {/* Animated glow on selection */}
                    {isSelected && (
                      <motion.div
                        className="absolute inset-0 rounded-lg"
                        style={{
                          boxShadow: "0 0 30px hsl(150 100% 50% / 0.5)",
                        }}
                        animate={{
                          opacity: [0.5, 1, 0.5],
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          ease: "easeInOut",
                        }}
                      />
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </motion.div>
      </div>
    </section>
  )
}

