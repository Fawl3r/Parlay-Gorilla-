"use client"

import type { ReactNode } from "react"
import type { LucideIcon } from "lucide-react"
import { motion } from "framer-motion"

import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"

export function LegalPageLayout({
  icon: Icon,
  title,
  lastUpdated,
  children,
}: {
  icon: LucideIcon
  title: ReactNode
  lastUpdated: string
  children: ReactNode
}) {
  return (
    <div className="min-h-screen flex flex-col bg-[#0a0a0f]">
      <Header />

      <main className="flex-1 py-20">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Header */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-green-600 mb-6">
              <Icon className="h-8 w-8 text-black" />
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-black mb-4">{title}</h1>
            <p className="text-gray-400">Last Updated: {lastUpdated}</p>
          </motion.div>

          {/* Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="space-y-8"
          >
            {children}
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  )
}


