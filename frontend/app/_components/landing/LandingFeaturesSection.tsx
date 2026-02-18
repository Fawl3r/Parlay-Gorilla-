"use client"

import { motion } from "framer-motion"
import { BarChart3, Brain, Shield, Target, Trophy, Zap } from "lucide-react"
import { getCopy, getCopyObject } from "@/lib/content"

export function LandingFeaturesSection() {
  return (
    <section
      id="features"
      className="py-10 md:py-12 border-t border-[#00FF5E]/40 bg-[#0A0F0A]/50 backdrop-blur-sm relative z-30"
    >
      <div className="container mx-auto px-4 md:px-8 max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-10"
        >
          <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight mb-2">
            {getCopy("site.home.features.title")}
          </h2>
          <p className="text-sm text-white/60 max-w-xl mx-auto">
            {getCopy("site.home.features.subtitle")}
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          {getCopyObject("site.home.features.items").map((item: any, index: number) => {
            const icons = [Brain, Zap, Shield, Target, Trophy, BarChart3]
            const gradients = [
              "from-purple-500 to-pink-500",
              "from-yellow-500 to-orange-500",
              "from-[#00FF5E] to-[#22FF6E]",
              "from-blue-500 to-cyan-500",
              "from-[#00FF5E] to-[#00FF5E]",
              "from-amber-500 to-yellow-500",
            ]
            return {
              icon: icons[index] || Brain,
              title: item.title,
              description: item.description,
              gradient: gradients[index] || "from-purple-500 to-pink-500",
            }
          }).map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="group p-6 rounded-xl bg-white/[0.02] border border-white/10 hover:border-[#00FF5E]/50 transition-all duration-300 hover:bg-white/[0.05] hover:shadow-lg"
              style={{
                boxShadow: "0 0 6px #00FF5E / 0.2",
              }}
            >
              <div
                className={`inline-flex p-2.5 rounded-lg bg-gradient-to-br ${feature.gradient} mb-4 group-hover:scale-105 transition-transform`}
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


