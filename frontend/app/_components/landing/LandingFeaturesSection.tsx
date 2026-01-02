"use client"

import { motion } from "framer-motion"
import { BarChart3, Brain, Shield, Target, Trophy, Zap } from "lucide-react"

export function LandingFeaturesSection() {
  return (
    <section
      id="features"
      className="py-24 border-t-2 border-[#00FF5E]/40 bg-[#0A0F0A]/50 backdrop-blur-sm relative z-30"
    >
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
              className="text-[#00FF5E]"
              style={{
                textShadow: "0 0 4px rgba(0, 255, 94, 0.7), 0 0 7px rgba(0, 204, 75, 0.5)",
              }}
            >
              Parlay Gorilla
            </span>
            <span className="text-white">?</span>
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto font-medium">
            Practical AI insights to help you evaluate matchups and build parlays with context.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              icon: Brain,
              title: "AI Insights",
              description:
                "See probability estimates, matchup context, and plain-English explanations for each leg—so you understand the “why,” not just the pick.",
              gradient: "from-purple-500 to-pink-500",
            },
            {
              icon: Zap,
              title: "Fast Parlay Builder",
              description:
                "Generate 1–20 leg parlay ideas in seconds. Adjust legs, sports, and risk preference to explore different scenarios.",
              gradient: "from-yellow-500 to-orange-500",
            },
            {
              icon: Shield,
              title: "Risk Indicators",
              description:
                "Choose conservative, balanced, or high-risk profiles. We surface risk indicators so you can decide what scenarios are worth analyzing.",
              gradient: "from-[#00FF5E] to-[#22FF6E]",
            },
            {
              icon: Target,
              title: "Major Sports Coverage",
              description:
                "Build across NFL, NBA, NHL, MLB, and more. Mix sports when it makes sense and keep your slip organized.",
              gradient: "from-blue-500 to-cyan-500",
            },
            {
              icon: Trophy,
              title: "Odds Comparison",
              description:
                "Compare odds across major platforms for informational purposes. Parlay Gorilla is not affiliated with any sportsbook and does not facilitate wagering.",
              gradient: "from-[#00FF5E] to-[#00FF5E]",
            },
            {
              icon: BarChart3,
              title: "Track Your Results",
              description:
                "Save parlays and review outcomes over time to learn what works for you. No hype—just feedback and iteration.",
              gradient: "from-amber-500 to-yellow-500",
            },
          ].map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="group p-8 rounded-2xl bg-white/[0.02] border border-white/10 hover:border-[#00FF5E]/50 transition-all duration-300 hover:bg-white/[0.05] hover:shadow-lg"
              style={{
                boxShadow: "0 0 6px #00FF5E / 0.2",
              }}
            >
              <div
                className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${feature.gradient} mb-5 group-hover:scale-110 transition-transform`}
              >
                <feature.icon className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-gray-400 leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}


