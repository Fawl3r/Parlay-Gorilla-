"use client"

import { motion } from "framer-motion"
import { Book, Zap, Shield, Target, Trophy, BarChart3, ArrowRight, Check } from "lucide-react"
import Link from "next/link"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"

export default function DocsPage() {
  return (
    <div className="min-h-screen flex flex-col bg-[#0a0a0f]">
      <Header />
      
      <main className="flex-1 py-20">
        <div className="container mx-auto px-4 max-w-5xl">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-green-600 mb-6">
              <Book className="h-8 w-8 text-black" />
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-black mb-4">
              <span className="text-white">Documentation</span>
            </h1>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Everything you need to know about using Parlay Gorilla to build winning parlays
            </p>
          </motion.div>

          {/* Quick Start */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mb-16"
          >
            <h2 className="text-3xl font-bold text-white mb-6">Quick Start</h2>
            <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <ol className="space-y-6">
                {[
                  {
                    step: "1",
                    title: "Create Your Account",
                    description: "Sign up for free - no credit card required. It takes less than 30 seconds."
                  },
                  {
                    step: "2",
                    title: "Choose Your Sport",
                    description: "Pick from NFL, NBA, NHL, MLB, UFC, or mix multiple sports for better diversification."
                  },
                  {
                    step: "3",
                    title: "Select Your Risk Level",
                    description: "Choose Safe (higher chance to hit), Balanced (good mix), or Degen (bigger payouts)."
                  },
                  {
                    step: "4",
                    title: "Pick Your Legs",
                    description: "Decide how many picks you want in your parlay - anywhere from 1 to 20 legs."
                  },
                  {
                    step: "5",
                    title: "Get Your Picks",
                    description: "Our AI will show you the best parlay picks with clear explanations. Copy and bet!"
                  }
                ].map((item) => (
                  <li key={item.step} className="flex gap-4">
                    <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-green-600 text-black font-black flex items-center justify-center">
                      {item.step}
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white mb-1">{item.title}</h3>
                      <p className="text-gray-400">{item.description}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          </motion.section>

          {/* Features Guide */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="mb-16"
          >
            <h2 className="text-3xl font-bold text-white mb-6">Features Guide</h2>
            <div className="grid md:grid-cols-2 gap-6">
              {[
                {
                  icon: Zap,
                  title: "Instant Parlays",
                  description: "Get ready-to-bet parlays in seconds. Our AI does all the research so you don't have to.",
                  tips: [
                    "Select your sport and risk level",
                    "Choose how many legs you want",
                    "Review the picks and explanations",
                    "Copy the parlay to your sportsbook"
                  ]
                },
                {
                  icon: Shield,
                  title: "Risk Levels",
                  description: "Choose the risk level that matches your betting style.",
                  tips: [
                    "Safe: Higher chance to hit, smaller payouts",
                    "Balanced: Good mix of safety and payout",
                    "Degen: Lower chance but much bigger payouts"
                  ]
                },
                {
                  icon: Target,
                  title: "Multi-Sport Parlays",
                  description: "Mix different sports to spread your risk and find better value.",
                  tips: [
                    "Select multiple sports when building",
                    "Our AI finds the best picks across all sports",
                    "Better diversification = more consistent wins"
                  ]
                },
                {
                  icon: Trophy,
                  title: "Live Odds",
                  description: "Always see the latest odds from all major sportsbooks.",
                  tips: [
                    "Odds update automatically",
                    "Compare odds across different books",
                    "Never miss a line change"
                  ]
                },
                {
                  icon: BarChart3,
                  title: "Track Your Wins",
                  description: "See which parlays hit and learn what works for you.",
                  tips: [
                    "View all your past parlays",
                    "See your win rate over time",
                    "Identify which sports and risk levels work best"
                  ]
                },
                {
                  icon: Book,
                  title: "AI Explanations",
                  description: "Every pick comes with a clear explanation of why it's strong.",
                  tips: [
                    "Read why each pick is recommended",
                    "Learn what factors matter most",
                    "Build your betting knowledge over time"
                  ]
                }
              ].map((feature, index) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + index * 0.1 }}
                  className="bg-white/[0.02] border border-white/10 rounded-xl p-6 hover:border-emerald-500/50 transition-all"
                >
                  <div className="inline-flex p-3 rounded-lg bg-gradient-to-br from-emerald-500 to-green-600 mb-4">
                    <feature.icon className="h-6 w-6 text-black" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">{feature.title}</h3>
                  <p className="text-gray-400 mb-4">{feature.description}</p>
                  <ul className="space-y-2">
                    {feature.tips.map((tip, tipIndex) => (
                      <li key={tipIndex} className="flex items-start gap-2 text-sm text-gray-400">
                        <Check className="h-4 w-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </motion.div>
              ))}
            </div>
          </motion.section>

          {/* Tips & Best Practices */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="mb-16"
          >
            <h2 className="text-3xl font-bold text-white mb-6">Tips & Best Practices</h2>
            <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <div className="space-y-6">
                {[
                  {
                    title: "Start with Safe Parlays",
                    content: "If you're new, start with Safe risk level parlays. They have a higher chance to hit and help you build confidence."
                  },
                  {
                    title: "Mix Sports for Better Results",
                    content: "Don't just stick to one sport. Mixing NFL, NBA, and NHL spreads your risk and often finds better value."
                  },
                  {
                    title: "Read the Explanations",
                    content: "Our AI tells you why each pick is strong. Understanding the reasoning helps you make better decisions."
                  },
                  {
                    title: "Track Your Performance",
                    content: "Use the Analytics section to see what works for you. Maybe you're better at certain sports or risk levels."
                  },
                  {
                    title: "Don't Chase Losses",
                    content: "If a parlay misses, don't immediately try to make it back with a bigger bet. Stick to your strategy."
                  },
                  {
                    title: "Shop for the Best Odds",
                    content: "We show odds from multiple books. Always check if you can get better odds elsewhere before placing your bet."
                  }
                ].map((tip, index) => (
                  <div key={index} className="flex gap-4">
                    <div className="flex-shrink-0 w-2 h-2 rounded-full bg-emerald-400 mt-2" />
                    <div>
                      <h3 className="text-lg font-bold text-white mb-1">{tip.title}</h3>
                      <p className="text-gray-400">{tip.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.section>

          {/* Getting Help */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="text-center"
          >
            <div className="bg-gradient-to-br from-emerald-950/50 to-cyan-950/50 border border-emerald-500/20 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">Still Need Help?</h2>
              <p className="text-gray-400 mb-6">
                Can't find what you're looking for? Our support team is here to help.
              </p>
              <Link
                href="/support"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-lg hover:from-emerald-400 hover:to-green-400 transition-all"
              >
                Contact Support
                <ArrowRight className="h-5 w-5" />
              </Link>
            </div>
          </motion.section>
        </div>
      </main>
      
      <Footer />
    </div>
  )
}

