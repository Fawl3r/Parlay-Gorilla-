"use client"

import { motion } from "framer-motion"
import { BadgeCheck, Fingerprint, Lock, ShieldCheck } from "lucide-react"

import { SECTION_ANIM } from "@/app/pg-101/_components/animations"
import { NeonCard } from "@/app/pg-101/_components/NeonCard"

export function VerificationRecordsSection() {
  return (
    <section id="verification" className="py-16 md:py-20 border-t border-white/5 bg-black/20">
      <div className="container mx-auto px-4">
        <motion.div {...SECTION_ANIM} className="mb-10 md:mb-12">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/40 px-4 py-2 backdrop-blur-md">
            <BadgeCheck className="h-4 w-4 text-[#00FF5E]" />
            <span className="text-sm text-white/80">Time-stamped verification</span>
          </div>
          <h2 className="mt-4 text-3xl md:text-5xl font-black text-white">
            Your parlay gets a <span className="text-neon">tamper-proof receipt</span>
          </h2>
          <p className="mt-3 text-gray-400 max-w-3xl leading-relaxed">
            When you save a <span className="text-white/90 font-semibold">Custom Parlay</span> and choose to verify it, Parlay Gorilla creates a
            permanent, time-stamped record confirming when this parlay was generated.
          </p>
          <p className="mt-3 text-gray-400 max-w-3xl leading-relaxed">
            <span className="text-emerald-200 font-semibold">Privacy first:</span> we do <span className="text-white/80">not</span>{" "}
            store emails, names, or personal details in the verification record. It contains only a non-identifying{" "}
            <span className="text-white/85 font-semibold">account number</span> and your parlay's fingerprint hash.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <motion.div {...SECTION_ANIM} transition={{ delay: 0.05 }}>
            <NeonCard
              icon={Fingerprint}
              title="What gets recorded"
              description="A verification record, not your entire slip. Think of it like a receipt that proves your parlay existed at that moment."
              bullets={[
                "A fingerprint hash (one-way; doesn't reveal your picks)",
                "Your anonymous account number (non-PII identifier)",
                "A timestamp + reference id for viewing the record",
              ]}
            />
          </motion.div>

          <motion.div {...SECTION_ANIM} transition={{ delay: 0.08 }}>
            <NeonCard
              icon={ShieldCheck}
              title="Why this is useful"
              description="It adds trust and transparency without exposing your strategy."
              bullets={[
                "Proof-of-creation for sharing and bragging rights",
                "Tamper-resistant record (changes would create a new fingerprint)",
                "Permanent record that can be referenced later",
              ]}
            />
          </motion.div>

          <motion.div {...SECTION_ANIM} transition={{ delay: 0.11 }}>
            <NeonCard
              icon={Lock}
              title="System-level integrity"
              description="The verification system is designed to create tamper-resistant records with minimal data exposure."
              bullets={[
                "Efficient storage for verification payloads",
                "Fast, low-friction verification workflow",
                "Built for reliability and integrity",
              ]}
            />
          </motion.div>
        </div>

        <motion.div {...SECTION_ANIM} transition={{ delay: 0.14 }} className="mt-8">
          <div className="rounded-3xl border border-white/10 bg-black/35 backdrop-blur-xl p-6 md:p-7">
            <div className="text-white font-black text-xl">Automatic verification</div>
            <ol className="mt-4 grid gap-3 text-sm text-gray-300 leading-relaxed">
              {[
                "Every Custom AI parlay is automatically verified when you generate it.",
                "Verification happens server-side — no action required from you.",
                "View verification records from your analysis results.",
                "The record contains only your account number and parlay fingerprint. No email or personal info is included.",
              ].map((step) => (
                <li key={step} className="flex gap-3">
                  <span className="mt-0.5 h-6 w-6 rounded-full bg-[#00FF5E]/15 border border-[#00FF5E]/25 text-emerald-200 flex items-center justify-center text-xs font-bold">
                    ✓
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>

            <div className="mt-6 text-xs text-gray-400">
              Verification creates a tamper-resistant record for your reference. This does not place bets and does not store personal data.
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}


