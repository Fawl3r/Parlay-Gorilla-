"use client"

import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { ArrowRight, CheckCircle } from "lucide-react"

import { ProviderLabel } from "./ProviderLabel"

export function ParlayPurchaseSuccessPanel({ provider }: { provider: string | null }) {
  const router = useRouter()

  return (
    <>
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", delay: 0.2 }}
        className="mx-auto w-24 h-24 rounded-full bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center mb-8 border-2 border-blue-500/50"
      >
        <CheckCircle className="h-12 w-12 text-blue-300" />
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="text-3xl md:text-4xl font-black text-white mb-4"
      >
        Thank You for{" "}
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-300 to-cyan-300">
          Your Purchase!
        </span>
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="text-gray-300 text-lg mb-2"
      >
        Your one-time parlay purchase is ready to use. Start building winning parlays now!
      </motion.p>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="text-gray-400 text-base mb-8"
      >
        Access your content below to get started.
      </motion.p>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }}>
        <button
          onClick={() => router.push("/app")}
          className="w-full py-4 px-6 bg-gradient-to-r from-blue-500 to-cyan-400 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-blue-500/20 transition-all flex items-center justify-center gap-2"
        >
          Access Your Content
          <ArrowRight className="h-5 w-5" />
        </button>
      </motion.div>

      <ProviderLabel provider={provider} />
    </>
  )
}


