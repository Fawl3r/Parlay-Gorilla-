"use client"

import { motion } from "framer-motion"

export function LandingHowItWorksSection() {
  return (
    <section
      id="how-it-works"
      className="py-24 border-t-2 border-[#00DD55]/40 bg-[#0A0F0A]/60 backdrop-blur-sm relative z-30"
    >
      <div className="container mx-auto px-4">
        <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black mb-6">
            <span className="text-white">How It </span>
            <span
              className="text-[#00DD55]"
              style={{
                textShadow: "0 0 4px rgba(0, 221, 85, 0.7), 0 0 7px rgba(0, 187, 68, 0.5)",
              }}
            >
              Works
            </span>
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto font-medium">Get started in three simple steps</p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {[
            {
              step: "01",
              title: "Sign Up Free",
              description: "Create your account in seconds. No credit card needed to get started.",
            },
            {
              step: "02",
              title: "Set Your Preferences",
              description: "Pick your sport(s), number of legs (1–20), and a risk profile to explore different scenarios.",
            },
            {
              step: "03",
              title: "Review AI Insights",
              description:
                "Get probability estimates and explanations. Use the info as decision support and make your own call.",
            },
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
                  boxShadow: "0 0 6px #00DD55, 0 0 12px #00BB44",
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
  )
}


