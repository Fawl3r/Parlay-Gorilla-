"use client"

import { TrendingUp, Zap, Shield, BarChart3, Trophy, Target, Activity } from "lucide-react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { GlowButton } from "@/components/ui/glow-button"
import { staggerContainer, staggerItem } from "@/lib/animations"

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b-2 border-primary/30 py-20 md:py-32 min-h-screen flex items-center">
      {/* Enhanced Dark Overlay for Readability */}
      <div className="absolute inset-0 dark-overlay z-0 opacity-40" />
      
      {/* Fullscreen Gorilla Silhouette Effect */}
      <div className="absolute inset-0 z-0 flex items-center justify-center">
        <motion.div
          className="absolute w-full h-full max-w-4xl max-h-[80vh] opacity-10"
          style={{
            backgroundImage: "url('/parlay-gorilla.png.webp')",
            backgroundSize: "contain",
            backgroundPosition: "center",
            backgroundRepeat: "no-repeat",
            filter: "brightness(0) invert(1)",
          }}
          animate={{
            scale: [1, 1.02, 1],
            opacity: [0.08, 0.12, 0.08],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </div>

      <div className="container relative z-10 px-4">
        <motion.div
          className="mx-auto max-w-4xl text-center"
          variants={staggerContainer}
          initial="initial"
          animate="animate"
        >
          <motion.div
            variants={staggerItem}
            className="mb-8 inline-flex items-center gap-2 rounded-full border-2 border-primary/50 bg-gradient-to-r from-primary/20 to-secondary/20 px-6 py-3 backdrop-blur-sm team-badge neon-glow-effect"
          >
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            >
              <Trophy className="h-5 w-5 text-primary" />
            </motion.div>
            <span className="text-sm font-bold text-foreground">
              AI-Powered Parlay Engine
            </span>
            <div className="h-4 w-px bg-primary/50" />
            <span className="text-xs font-semibold text-primary animate-pulse">LIVE</span>
          </motion.div>
          
          <motion.h1
            variants={staggerItem}
            className="mb-6 text-6xl font-black tracking-tight sm:text-7xl md:text-8xl lg:text-9xl"
          >
            <motion.span 
              className="block font-black text-foreground mb-2"
              animate={{
                textShadow: [
                  "0 0 20px hsl(150 100% 50% / 0.3)",
                  "0 0 40px hsl(150 100% 50% / 0.5), 0 0 60px hsl(199 89% 48% / 0.3)",
                  "0 0 20px hsl(150 100% 50% / 0.3)",
                ],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            >
              Build Winning
            </motion.span>
            <motion.span 
              className="block gradient-text font-black"
              animate={{
                scale: [1, 1.02, 1],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            >
              Parlays
            </motion.span>
            <motion.span 
              className="block text-4xl sm:text-5xl md:text-6xl mt-4 text-foreground/90 font-bold"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.8 }}
            >
              AI Intelligence That Wins
            </motion.span>
          </motion.h1>
          
          <motion.p
            variants={staggerItem}
            className="mb-10 text-lg text-foreground/90 sm:text-xl max-w-2xl mx-auto leading-relaxed font-medium"
          >
            Generate optimized 1–20 leg parlays with win probabilities, confidence scores, and detailed AI explanations. 
            Mix NFL, NBA, and NHL for maximum diversification and edge.
          </motion.p>

          <motion.div
            variants={staggerItem}
            className="flex flex-col gap-4 sm:flex-row sm:justify-center mb-16"
          >
            <GlowButton size="lg" variant="neon" className="text-base px-8 py-6 text-lg font-semibold">
              <TrendingUp className="mr-2 h-5 w-5" />
              Start Building Parlays
            </GlowButton>
            <Button size="lg" variant="outline" className="text-base px-8 py-6 text-lg border-2">
              <BarChart3 className="mr-2 h-5 w-5" />
              View Analytics
            </Button>
          </motion.div>
        </motion.div>

        {/* Premium Feature Cards */}
        <motion.div
          className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
          variants={staggerContainer}
          initial="initial"
          animate="animate"
        >
          {[
            {
              icon: Zap,
              title: "Lightning Fast",
              description: "Generate optimized parlays in seconds with advanced algorithms",
              gradient: "from-primary/20 to-primary/10",
            },
            {
              icon: Shield,
              title: "Risk Management",
              description: "Safe, Balanced, and Degen profiles with confidence scoring",
              gradient: "from-secondary/20 to-secondary/10",
            },
            {
              icon: TrendingUp,
              title: "Multi-Sport",
              description: "Mix NFL, NBA, and NHL for better diversification",
              gradient: "from-primary/20 to-secondary/10",
            },
            {
              icon: Target,
              title: "Precision Picks",
              description: "ML-calibrated probabilities with visual confidence indicators",
              gradient: "from-secondary/20 to-accent/10",
            },
            {
              icon: Activity,
              title: "Real-Time Data",
              description: "Live odds updates and market analysis powered by The Odds API",
              gradient: "from-primary/20 to-secondary/15",
            },
            {
              icon: Trophy,
              title: "Win Tracking",
              description: "Track your parlay performance and optimize your strategy",
              gradient: "from-secondary/20 to-accent/15",
            },
          ].map((feature) => (
            <motion.div key={feature.title} variants={staggerItem}>
              <Card className="group relative overflow-hidden border-2 border-primary/30 transition-all duration-300 hover:border-primary/60 card-elevated hover:card-elevated-hover h-full neon-glow-effect">
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
                <div className="absolute inset-0 circuit-pattern opacity-0 group-hover:opacity-30 transition-opacity" />
                <CardContent className="relative p-6">
                  <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-gradient-to-br from-primary/30 to-secondary/30 group-hover:from-primary/40 group-hover:to-secondary/40 transition-all duration-300 team-badge">
                    <feature.icon className="h-8 w-8 text-primary" />
                  </div>
                  <h3 className="mb-2 text-lg font-bold text-foreground">{feature.title}</h3>
                  <p className="text-sm text-foreground/80 leading-relaxed">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}

