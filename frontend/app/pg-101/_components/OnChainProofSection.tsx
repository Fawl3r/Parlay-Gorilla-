"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { BadgeCheck, Fingerprint, Lock, ShieldCheck } from "lucide-react"

import { SECTION_ANIM } from "@/app/pg-101/_components/animations"
import { NeonCard } from "@/app/pg-101/_components/NeonCard"

export function OnChainProofSection() {
  return (
    <section id="onchain" className="py-16 md:py-20 border-t border-white/5 bg-black/20">
      <div className="container mx-auto px-4">
        <motion.div {...SECTION_ANIM} className="mb-10 md:mb-12">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/40 px-4 py-2 backdrop-blur-md">
            <BadgeCheck className="h-4 w-4 text-[#00DD55]" />
            <span className="text-sm text-white/80">Proof-of-creation (on-chain)</span>
          </div>
          <h2 className="mt-4 text-3xl md:text-5xl font-black text-white">
            Your parlay gets a <span className="text-neon">tamper-proof receipt</span>
          </h2>
          <p className="mt-3 text-gray-400 max-w-3xl leading-relaxed">
            When you save a <span className="text-white/90 font-semibold">Custom Parlay</span>, Parlay Gorilla creates a
            cryptographic fingerprint (a “hash”) of your parlay and anchors a proof on{" "}
            <span className="text-white/85">Solana</span>—a public blockchain that acts like a global, timestamped ledger.
          </p>
          <p className="mt-3 text-gray-400 max-w-3xl leading-relaxed">
            <span className="text-emerald-200 font-semibold">Privacy first:</span> we do <span className="text-white/80">not</span>{" "}
            inscribe emails, names, or personal details. The on-chain proof contains only a non-identifying{" "}
            <span className="text-white/85 font-semibold">account number</span> and your parlay’s fingerprint hash.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <motion.div {...SECTION_ANIM} transition={{ delay: 0.05 }}>
            <NeonCard
              icon={Fingerprint}
              title="What gets written to the blockchain"
              description="A proof, not your entire slip. Think of it like a receipt that proves your parlay existed at that moment."
              bullets={[
                "A fingerprint hash (one-way; doesn’t reveal your picks)",
                "Your anonymous account number (non-PII identifier)",
                "A timestamp + reference id for verification",
              ]}
            />
          </motion.div>

          <motion.div {...SECTION_ANIM} transition={{ delay: 0.08 }}>
            <NeonCard
              icon={ShieldCheck}
              title="Why this is a great feature"
              description="It adds trust and transparency without exposing your strategy."
              bullets={[
                "Proof-of-creation for sharing and bragging rights",
                "Tamper-resistant record (changes would create a new hash)",
                "Verifiable by anyone via a public explorer (Solscan)",
              ]}
            />
          </motion.div>

          <motion.div {...SECTION_ANIM} transition={{ delay: 0.11 }}>
            <NeonCard
              icon={Lock}
              title="Why we used Code‑In (IQ Labs)"
              description="We use IQ Labs’ Code‑In inscription method because it’s purpose-built for lightweight on-chain inscriptions."
              bullets={[
                "Efficient on-chain storage for “proof” payloads",
                "Fast, low-friction verification workflows",
                "Built by the IQ Labs development team (see their whitepaper)",
              ]}
            />
          </motion.div>
        </div>

        <motion.div {...SECTION_ANIM} transition={{ delay: 0.14 }} className="mt-8">
          <div className="rounded-3xl border border-white/10 bg-black/35 backdrop-blur-xl p-6 md:p-7">
            <div className="text-white font-black text-xl">How to verify (super simple)</div>
            <ol className="mt-4 grid gap-3 text-sm text-gray-300 leading-relaxed">
              {[
                "Save a Custom Parlay (it will show “On-chain” in Saved Parlays).",
                "Wait for the status to turn “Confirmed”.",
                "Click “View on Solscan” — you’re looking at the public receipt transaction.",
                "The transaction contains the proof payload (account number + hash). No email or personal info is included.",
              ].map((step) => (
                <li key={step} className="flex gap-3">
                  <span className="mt-0.5 h-6 w-6 rounded-full bg-[#00DD55]/15 border border-[#00DD55]/25 text-emerald-200 flex items-center justify-center text-xs font-bold">
                    ✓
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>

            <div className="mt-6 text-xs text-gray-400">
              Want to learn more about the Code‑In creators? IQ Labs’ whitepaper credits the IQ Labs development team
              and lists <span className="text-gray-200">Kim Su‑Min (@im_zo_sol)</span> as the author. Read more at{" "}
              <Link
                href="https://iqlabs.dev/"
                target="_blank"
                rel="noreferrer"
                className="text-emerald-200 hover:text-emerald-100 underline underline-offset-4"
              >
                iqlabs.dev
              </Link>
              . This proof is a public receipt only—it doesn’t place bets and it doesn’t store personal data.
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}


