"use client";

import { motion } from "framer-motion";
import { Award, BarChart2, Target, TrendingUp, Wallet } from "lucide-react";

export function AffiliateBenefitsSection() {
  return (
    <section id="benefits" className="py-16 md:py-20">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-5xl font-black text-white mb-4">Why this converts</h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            The product is sticky, the hook is free, and the payouts scale with your audience.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {[
            {
              title: "High Conversion Product",
              description: "Sports bettors love our AI-powered parlays. Easy sell to your audience.",
              icon: BarChart2,
            },
            {
              title: "Recurring Revenue",
              description: "Unlock monthly recurring commissions at All-Star tier (and higher) for as long as referrals stay subscribed.",
              icon: TrendingUp,
            },
            {
              title: "30-Day Cookie",
              description: "Your referral link stays active for 30 days. No missed conversions.",
              icon: Target,
            },
            {
              title: "Real-Time Dashboard",
              description: "Track clicks, conversions, and earnings in your affiliate dashboard.",
              icon: BarChart2,
            },
            {
              title: "Fast Payouts",
              description: "Get paid monthly via PayPal once you reach the $25 minimum payout.",
              icon: Wallet,
            },
            {
              title: "Tier Upgrades",
              description: "Automatically unlock higher commission rates as you grow.",
              icon: Award,
            },
          ].map((benefit, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.05 }}
              className="flex items-start gap-4 p-5 rounded-2xl bg-black/35 border border-white/10 backdrop-blur-md"
            >
              <div className="p-2 bg-[#00FF5E]/10 border border-[#00FF5E]/25 rounded-xl shrink-0">
                <benefit.icon className="w-5 h-5 text-[#00FF5E]" />
              </div>
              <div>
                <h3 className="font-bold text-white mb-1">{benefit.title}</h3>
                <p className="text-sm text-gray-400">{benefit.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}



