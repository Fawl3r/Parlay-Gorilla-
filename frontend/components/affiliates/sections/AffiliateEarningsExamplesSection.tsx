"use client";

import { motion } from "framer-motion";

export function AffiliateEarningsExamplesSection() {
  return (
    <section className="py-16 md:py-20">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-5xl font-black text-white mb-4">Earning potential</h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            See how much you could earn with just a few referrals.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {[
            {
              referrals: 10,
              scenario: "Casual Promoter",
              monthly: "$80",
              yearly: "$960+",
              description: "10 new subscribers this month (20% first payment)",
            },
            {
              referrals: 50,
              scenario: "Active Influencer",
              monthly: "$500",
              yearly: "$6,000+",
              description: "50 new subscribers this month (Pro tier 25%)",
            },
            {
              referrals: 200,
              scenario: "Top Affiliate",
              monthly: "$3,200+",
              yearly: "$38,400+",
              description: "Hall of Fame tier (40%) + recurring + credit packs",
            },
          ].map((example, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="p-6 rounded-2xl bg-black/35 border border-white/10 backdrop-blur-md text-center"
            >
              <div className="text-4xl font-black text-[#00FF5E] mb-2">{example.monthly}</div>
              <div className="text-sm text-gray-400 mb-4">per month</div>
              <h3 className="text-lg font-bold text-white mb-2">{example.scenario}</h3>
              <p className="text-sm text-gray-400 mb-4">{example.description}</p>
              <div className="text-xs text-emerald-200">{example.yearly} potential yearly</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}



