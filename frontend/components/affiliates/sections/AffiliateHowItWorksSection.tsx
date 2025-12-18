"use client";

import { motion } from "framer-motion";
import { Gift, Share2, Users, Wallet } from "lucide-react";

export function AffiliateHowItWorksSection() {
  return (
    <section id="how" className="py-16 md:py-20">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-5xl font-black text-white mb-4">How it works (simple)</h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Four simple steps to start earning passive income from your sports network.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 max-w-5xl mx-auto">
          {[
            {
              step: 1,
              title: "Join the Program",
              description: "Sign up for free and get your unique Gorilla referral link instantly.",
              icon: Users,
            },
            {
              step: 2,
              title: "Share Your Link",
              description: "Share with friends, followers, or your sports community.",
              icon: Share2,
            },
            {
              step: 3,
              title: "They Get 2 Free Parlays",
              description: "Your referrals start with 2 free AI-powered parlay generations.",
              icon: Gift,
            },
            {
              step: 4,
              title: "You Get Paid",
              description: "Earn commission when they subscribe or buy credits.",
              icon: Wallet,
            },
          ].map((item, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="relative"
            >
              {index < 3 && (
                <div className="hidden md:block absolute top-12 left-[60%] w-[80%] h-0.5 bg-gradient-to-r from-[#00DD55]/50 to-transparent" />
              )}

              <div className="p-6 rounded-2xl bg-black/35 border border-white/10 backdrop-blur-md relative">
                <div className="absolute -top-3 -left-3 w-8 h-8 bg-[#00DD55] text-black font-black rounded-full flex items-center justify-center text-sm">
                  {item.step}
                </div>

                <div className="p-3 bg-[#00DD55]/10 border border-[#00DD55]/25 rounded-xl w-fit mb-4">
                  <item.icon className="w-6 h-6 text-[#00DD55]" />
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{item.title}</h3>
                <p className="text-sm text-gray-400">{item.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}



