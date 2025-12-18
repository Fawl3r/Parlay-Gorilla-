"use client";

import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";

export type AffiliateCTASectionProps = {
  ctaText: string;
  onJoinClick: () => void;
};

export function AffiliateCTASection({ ctaText, onJoinClick }: AffiliateCTASectionProps) {
  return (
    <section className="py-20 md:py-24 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_0%,rgba(0,221,85,0.22),transparent_55%),radial-gradient(circle_at_85%_60%,rgba(34,221,102,0.14),transparent_60%)]" />

      <div className="container mx-auto px-4 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-2xl mx-auto text-center"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-[#00DD55]/25 bg-black/35 px-4 py-2 backdrop-blur-md mb-6">
            <Sparkles className="h-4 w-4 text-[#00DD55]" />
            <span className="text-sm text-emerald-200 font-semibold">Join the Gorilla Squad</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-black text-white mb-4">
            Ready to Start <span className="text-neon-strong">earning?</span>
          </h2>
          <p className="text-gray-400 mb-8">
            Join the Gorilla Squad today and turn your sports network into passive income.
          </p>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onJoinClick}
            className="glow-neon px-10 py-4 bg-[#00DD55] text-black font-black rounded-xl hover:bg-[#22DD66] transition-all flex items-center justify-center gap-2 mx-auto"
          >
            {ctaText}
            <ArrowRight className="w-5 h-5" />
          </motion.button>

          <p className="mt-4 text-sm text-gray-500">Free to join • No minimum payout • Instant access</p>
        </motion.div>
      </div>
    </section>
  );
}



