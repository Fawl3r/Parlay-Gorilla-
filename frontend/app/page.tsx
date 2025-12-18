"use client"

import { motion, useScroll, useTransform } from "framer-motion"
import { useRef, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import Image from "next/image"
import { Zap, Shield, BarChart3, Sparkles, ArrowRight, Check, Target, Trophy, Brain } from "lucide-react"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import SportsShowcase from "@/components/SportsShowcase"
import { api } from "@/lib/api"

// Pre-generate particle positions to avoid hydration mismatch
function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000
  return x - Math.floor(x)
}

export default function LandingPage() {
  const [mounted, setMounted] = useState(false)
  
  // Memoize particle positions with deterministic values
  const particlePositions = useMemo(() => 
    [...Array(15)].map((_, i) => ({
      // Round to 4 decimals to match SSR/client formatting and avoid hydration mismatches.
      left: `${(40 + seededRandom(i * 2) * 20).toFixed(4)}%`,
      top: `${(40 + seededRandom(i * 2 + 1) * 20).toFixed(4)}%`,
      xOffset: seededRandom(i * 3) * 50 - 25,
      duration: 3 + seededRandom(i * 4) * 2,
      delay: seededRandom(i * 5) * 2,
    })), []
  )
  const heroRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"]
  })
  
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])
  
  // Trigger animations when page becomes visible (after age gate removal)
  useEffect(() => {
    setMounted(true)
    
    // Pre-warm the cache for faster app loads
    api.warmupCache()
    
    // Force a re-render to trigger animations after age gate is removed
    const checkVisibility = () => {
      if (!document.body.classList.contains('age-gate-active')) {
        // Trigger animations by forcing a small delay
        setTimeout(() => {
          window.dispatchEvent(new Event('resize'))
        }, 100)
      }
    }
    
    // Check immediately and on interval
    checkVisibility()
    const interval = setInterval(checkVisibility, 200)
    
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1">
        {/* Hero Section - Full Background Image */}
        <section 
          ref={heroRef} 
          className="relative min-h-screen flex items-center justify-center overflow-hidden"
          style={{
            backgroundImage: "url('/images/s1back.png')",
            backgroundSize: "cover",
            backgroundPosition: "center",
            backgroundRepeat: "no-repeat",
          }}
        >
          {/* Dark overlay for text readability - lighter to showcase background */}
          <div className="absolute inset-0 bg-black/30 z-10" />
          
          {/* Subtle gradient overlay for better text contrast */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-black/20 to-black/40 z-10" />
          
          {/* Additional radial gradient for center focus */}
          <div className="absolute inset-0 bg-radial-gradient from-transparent via-transparent to-black/20 z-10" 
            style={{
              background: 'radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,0.1) 50%, rgba(0,0,0,0.3) 100%)'
            }}
          />
          
          {/* Content Container */}
          <motion.div 
            className="container mx-auto px-4 relative z-20"
            initial={{ opacity: 0 }}
            animate={mounted ? { opacity: 1 } : { opacity: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            style={mounted ? { opacity } : { opacity: 0 }}
          >
            <div className="grid lg:grid-cols-2 gap-12 items-center min-h-[80vh]">
              {/* Left Column - Text Content */}
              <motion.div
                key={mounted ? 'mounted' : 'unmounted'}
                initial={{ opacity: 0, x: -50 }}
                animate={mounted ? { opacity: 1, x: 0 } : { opacity: 0, x: -50 }}
                transition={{ duration: 0.8, delay: 0.2 }}
                className="text-left lg:text-left"
              >
                {/* Badge with glow */}
                <motion.div 
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2 }}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#00DD55]/20 border border-[#00DD55]/50 mb-8 backdrop-blur-md relative overflow-hidden"
                  style={{
                    boxShadow: '0 0 6px #00DD55, 0 0 12px #00BB44'
                  }}
                >
                  <div className="absolute inset-0 bg-[#00DD55]/30 blur-xl" />
                  <Sparkles 
                    className="h-4 w-4 text-[#00DD55] relative z-10"
                    style={{
                      filter: 'drop-shadow(0 0 2px rgba(0, 221, 85, 0.5))'
                    }}
                  />
                  <span 
                    className="text-sm font-semibold text-white tracking-wide relative z-10"
                    style={{
                      textShadow: '0 0 3px rgba(0, 221, 85, 0.5)'
                    }}
                  >
                    Smart Parlay Picks
                  </span>
                </motion.div>
                
                {/* Main headline with animated gradient */}
                <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black mb-6 leading-[0.95] tracking-tight">
                  <motion.span 
                    className="block text-[#00DD55]"
                    style={{
                      textShadow: '0 0 4px rgba(0, 221, 85, 0.7), 0 0 7px rgba(0, 187, 68, 0.5)',
                      backgroundPosition: "0% 50%",
                      backgroundSize: "200% 200%"
                    }}
                    animate={{
                      backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"]
                    }}
                    transition={{
                      duration: 5,
                      repeat: Infinity,
                      ease: "linear"
                    }}
                  >
                    Build Winning
                  </motion.span>
                  <motion.span 
                    className="block text-[#00DD55] mt-2"
                    style={{
                      textShadow: '0 0 4px rgba(0, 221, 85, 0.7), 0 0 7px rgba(0, 187, 68, 0.5)'
                    }}
                  >
                    Parlays
                  </motion.span>
                  <span className="block text-white mt-4 text-4xl sm:text-5xl md:text-6xl font-bold">
                    With AI Intelligence
                  </span>
                </h1>
                
                {/* Subtext with better contrast */}
                <p className="text-lg sm:text-xl md:text-2xl text-white mb-10 max-w-2xl leading-relaxed font-medium">
                  Get winning <span 
                    className="text-[#00DD55] font-semibold"
                    style={{
                      textShadow: '0 0 3px rgba(0, 221, 85, 0.6)'
                    }}
                  >
                    parlay picks
                  </span> from 1 to 20 legs with 
                  our AI that tells you exactly why each pick is strong. 
                  Mix <span className="text-white font-semibold">NFL, NBA, and NHL</span> to build bigger, smarter bets.
                </p>
                
                {/* CTA Buttons with enhanced effects */}
                <div className="flex flex-col sm:flex-row gap-4 mb-6">
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="relative"
                  >
                    <div className="absolute inset-0 bg-[#00DD55] blur-xl opacity-60 rounded-xl" />
                    <Link 
                      href="/auth/signup"
                      className="relative inline-flex items-center gap-2 px-8 py-4 text-lg font-bold text-black bg-[#00DD55] rounded-xl hover:bg-[#22DD66] transition-all"
                      style={{
                        boxShadow: '0 0 6px #00DD55, 0 0 12px #00BB44, 0 0 20px #22DD66'
                      }}
                    >
                      Get Started Free
                      <ArrowRight className="h-5 w-5" />
                    </Link>
                  </motion.div>
                  
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Link 
                      href="/auth/login"
                      className="inline-flex items-center gap-2 px-8 py-4 text-lg font-semibold text-white bg-transparent border-2 border-[#00DD55] rounded-xl hover:bg-[#00DD55]/10 transition-all backdrop-blur-md"
                      style={{
                        boxShadow: '0 0 6px #00DD55 / 0.3'
                      }}
                    >
                      Sign In
                    </Link>
                  </motion.div>
                </div>
                
                <p className="text-sm text-white/60 font-medium">
                  No credit card required • Free to start
                </p>
              </motion.div>

              {/* Right Column - Enhanced Visual Effects */}
              <motion.div
                key={mounted ? 'mounted-right' : 'unmounted-right'}
                initial={{ opacity: 0, x: 50 }}
                animate={mounted ? { opacity: 1, x: 0 } : { opacity: 0, x: 50 }}
                transition={{ duration: 0.8, delay: 0.4 }}
                className="relative hidden lg:flex items-center justify-center"
              >
                <div className="relative w-full h-[600px] flex items-center justify-center">
                  {/* Hero Image - Seamlessly blended with background */}
                  <motion.div
                    className="absolute inset-0 flex items-center justify-center z-0"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 1.2, delay: 0.3, ease: "easeOut" }}
                  >
                    <div 
                      className="relative w-full h-full"
                      style={{
                        maskImage: "radial-gradient(ellipse 70% 70% at center, black 40%, transparent 75%)",
                        WebkitMaskImage: "radial-gradient(ellipse 70% 70% at center, black 40%, transparent 75%)",
                      }}
                    >
                      <Image
                        src="/images/hero.png"
                        alt="Parlay Gorilla Hero"
                        fill
                        className="object-contain"
                        priority
                        style={{
                          opacity: 0.9,
                          filter: "brightness(1.15) saturate(1.3) contrast(1.1)",
                        }}
                      />
                    </div>
                  </motion.div>

                  {/* Central Glow Effect */}
                  <motion.div
                    className="absolute inset-0 bg-[#00DD55]/20 rounded-full blur-[150px] z-10"
                    animate={{
                      scale: [1, 1.2, 1],
                      opacity: [0.3, 0.6, 0.3]
                    }}
                    transition={{
                      duration: 4,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                  />
                  
                  {/* Animated Circuit Board Pattern */}
                  <motion.div
                    className="absolute inset-0 opacity-30 z-10"
                    animate={{
                      backgroundPosition: ["0% 0%", "100% 100%"]
                    }}
                    transition={{
                      duration: 15,
                      repeat: Infinity,
                      ease: "linear"
                    }}
                    style={{
                      backgroundImage: `radial-gradient(circle, rgba(0, 255, 102, 0.4) 1px, transparent 1px)`,
                      backgroundSize: '40px 40px'
                    }}
                  />
                  
                  {/* Multiple Animated Glow Rings */}
                  {[1, 2, 3].map((ring, i) => (
                    <motion.div
                      key={ring}
                      className="absolute border-2 border-[#00DD55]/30 rounded-full z-10"
                      style={{
                        width: `${300 + i * 100}px`,
                        height: `${300 + i * 100}px`
                      }}
                      animate={{
                        scale: [1, 1.2 + i * 0.1, 1],
                        opacity: [0.2, 0.5, 0.2],
                        rotate: [0, 360]
                      }}
                      transition={{
                        duration: 4 + i,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: i * 0.5
                      }}
                    />
                  ))}
                  
                  {/* Floating Particles */}
                  {particlePositions.map((particle, i) => (
                    <motion.div
                      key={i}
                      className="absolute w-1 h-1 bg-[#00DD55] rounded-full z-20"
                      style={{
                        left: particle.left,
                        top: particle.top,
                      }}
                      animate={{
                        y: [0, -50, 0],
                        x: [0, particle.xOffset, 0],
                        opacity: [0, 1, 0],
                        scale: [0, 1, 0]
                      }}
                      transition={{
                        duration: particle.duration,
                        repeat: Infinity,
                        delay: particle.delay,
                        ease: "easeInOut"
                      }}
                    />
                  ))}
                </div>
              </motion.div>
            </div>
          </motion.div>
          
        </section>

        {/* Stats Section */}
        <section className="py-16 border-t-2 border-[#00DD55]/40 border-b-2 border-[#00DD55]/40 bg-[#0A0F0A]/70 backdrop-blur-sm relative z-30">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {[
                { value: "50K+", label: "Parlays Built" },
                { value: "68%", label: "Win Rate" },
                { value: "5+", label: "Sports" },
                { value: "Live", label: "Odds" }
              ].map((stat, index) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  className="text-center"
                >
                  <div 
                    className="text-3xl md:text-4xl font-black text-[#00DD55] mb-2"
                    style={{
                      textShadow: '0 0 4px rgba(0, 221, 85, 0.7), 0 0 7px rgba(0, 187, 68, 0.5)'
                    }}
                  >
                    {stat.value}
                  </div>
                  <div className="text-sm text-white font-medium drop-shadow-[0_0_4px_rgba(0,0,0,0.6)]">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Sports Showcase - Gorilla Fade-In Section */}
        <SportsShowcase />

        {/* Features Section */}
        <section id="features" className="py-24 border-t-2 border-[#00DD55]/40 bg-[#0A0F0A]/50 backdrop-blur-sm relative z-30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl md:text-5xl lg:text-6xl font-black mb-6">
                <span className="text-white">Why </span>
                <span 
                  className="text-[#00DD55]"
                  style={{
                    textShadow: '0 0 4px rgba(0, 221, 85, 0.7), 0 0 7px rgba(0, 187, 68, 0.5)'
                  }}
                >
                  Parlay Gorilla
                </span>
                <span className="text-white">?</span>
              </h2>
              <p className="text-xl text-gray-400 max-w-2xl mx-auto font-medium">
                Everything you need to build better bets and win more
              </p>
            </motion.div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                {
                  icon: Brain,
                  title: "Smart AI Picks",
                  description: "Our AI analyzes every game and tells you which picks have the best chance to hit. See exactly why each pick is strong before you bet.",
                  gradient: "from-purple-500 to-pink-500"
                },
                {
                  icon: Zap,
                  title: "Instant Parlays",
                  description: "Get ready-to-bet parlays in seconds. No research needed - we've done the work for you with the latest odds from all major sportsbooks.",
                  gradient: "from-yellow-500 to-orange-500"
                },
                {
                  icon: Shield,
                  title: "Bet Smart, Not Hard",
                  description: "Choose from Safe bets (higher chance to hit), Balanced (good mix), or Degen (bigger payouts). We show you the risk so you decide.",
                  gradient: "from-[#00DD55] to-[#22DD66]"
                },
                {
                  icon: Target,
                  title: "All Major Sports",
                  description: "Build parlays across NFL, NBA, NHL, MLB, UFC, and more. Mix sports to spread your risk and find the best value bets.",
                  gradient: "from-blue-500 to-cyan-500"
                },
                {
                  icon: Trophy,
                  title: "Live Odds",
                  description: "Always get the latest odds from FanDuel, DraftKings, BetMGM, and more. Never miss a line change that could make your bet better.",
                  gradient: "from-[#00DD55] to-[#00DD55]"
                },
                {
                  icon: BarChart3,
                  title: "Track Your Wins",
                  description: "See which parlays hit and which missed. Learn what works for you and build better bets over time.",
                  gradient: "from-amber-500 to-yellow-500"
                }
              ].map((feature, index) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="group p-8 rounded-2xl bg-white/[0.02] border border-white/10 hover:border-[#00DD55]/50 transition-all duration-300 hover:bg-white/[0.05] hover:shadow-lg"
                  style={{
                    boxShadow: '0 0 6px #00DD55 / 0.2'
                  }}
                >
                  <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${feature.gradient} mb-5 group-hover:scale-110 transition-transform`}>
                    <feature.icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                  <p className="text-gray-400 leading-relaxed">{feature.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section id="how-it-works" className="py-24 border-t-2 border-[#00DD55]/40 bg-[#0A0F0A]/60 backdrop-blur-sm relative z-30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl md:text-5xl lg:text-6xl font-black mb-6">
                <span className="text-white">How It </span>
                <span 
                  className="text-[#00DD55]"
                  style={{
                    textShadow: '0 0 4px rgba(0, 221, 85, 0.7), 0 0 7px rgba(0, 187, 68, 0.5)'
                  }}
                >
                  Works
                </span>
              </h2>
              <p className="text-xl text-gray-400 max-w-2xl mx-auto font-medium">
                Get started in three simple steps
              </p>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              {[
                {
                  step: "01",
                  title: "Sign Up Free",
                  description: "Create your account in seconds. No credit card needed - start building winning parlays right away."
                },
                {
                  step: "02",
                  title: "Pick Your Style",
                  description: "Choose your favorite sports, how risky you want to bet, and how many picks you want in your parlay (1-20)."
                },
                {
                  step: "03",
                  title: "Get Winning Picks",
                  description: "We'll show you the best parlay picks with clear explanations of why each one is strong. Copy and bet."
                }
              ].map((item, index) => (
                <motion.div
                  key={item.step}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.15 }}
                  className="relative text-center"
                >
                  {/* Connector line */}
                  {index < 2 && (
                    <div className="hidden md:block absolute top-10 left-[60%] w-[80%] h-0.5 bg-gradient-to-r from-[#00DD55]/50 to-transparent" />
                  )}
                  
                  <div 
                    className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-[#00DD55] text-black text-2xl font-black mb-6"
                    style={{
                      boxShadow: '0 0 6px #00DD55, 0 0 12px #00BB44'
                    }}
                  >
                    {item.step}
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">{item.title}</h3>
                  <p className="text-gray-400 leading-relaxed">{item.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-24 border-t-2 border-[#00DD55]/40 relative overflow-hidden z-30">
          {/* Background effects */}
          <div className="absolute inset-0 bg-[#0A0F0A]/70 backdrop-blur-sm" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#00DD55]/10 rounded-full blur-[120px]" />
          
          <div className="container mx-auto px-4 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center max-w-4xl mx-auto"
            >
              <h2 className="text-4xl md:text-5xl lg:text-6xl font-black mb-6">
                <span className="text-white">Ready to Build </span>
                <span 
                  className="text-[#00DD55]"
                  style={{
                    textShadow: '0 0 4px rgba(0, 221, 85, 0.7), 0 0 7px rgba(0, 187, 68, 0.5)'
                  }}
                >
                  Winning Parlays
                </span>
                <span className="text-white">?</span>
              </h2>
              <p className="text-xl text-gray-400 mb-10 font-medium">
                Join thousands of bettors winning more with our smart parlay picks
              </p>
              
              {/* Feature pills */}
              <div className="flex flex-wrap justify-center gap-3 mb-10">
                {[
                  "Unlimited parlay picks",
                  "Live odds from all books",
                  "Clear win chances",
                  "All major sports",
                  "Track what works"
                ].map((feature) => (
                  <div 
                    key={feature} 
                    className="flex items-center gap-2 px-4 py-2.5 rounded-full bg-white/5 border border-white/10"
                  >
                    <Check className="h-4 w-4 text-[#00DD55]" />
                    <span className="text-sm text-gray-300 font-medium">{feature}</span>
                  </div>
                ))}
              </div>
              
              <motion.div
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Link 
                  href="/auth/signup"
                  className="inline-flex items-center gap-2 px-10 py-5 text-xl font-bold text-black bg-[#00DD55] rounded-xl hover:bg-[#22DD66] transition-all"
                  style={{
                    boxShadow: '0 0 6px #00DD55, 0 0 12px #00BB44, 0 0 20px #22DD66'
                  }}
                >
                  Start Building Parlays Now
                  <ArrowRight className="h-6 w-6" />
                </Link>
              </motion.div>
            </motion.div>
          </div>
        </section>
      </main>
      
      <Footer />
    </div>
  )
}
