"use client"

import { TrendingUp, Menu, X } from "lucide-react"
import { useState } from "react"
import { motion } from "framer-motion"
import { GlowButton } from "@/components/ui/glow-button"
import { Button } from "@/components/ui/button"

const PRIMARY_NEON = "hsl(150, 100%, 50%)"

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 w-full border-b-2 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60 shadow-sm">
      <div className="container flex h-18 items-center justify-between px-4">
        <motion.div
          className="flex items-center gap-3"
          whileHover={{ scale: 1.02 }}
          transition={{ duration: 0.2 }}
        >
          <div
            className="relative flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent shadow-lg"
            style={{
              boxShadow: "0 4px 20px hsl(var(--primary) / 0.3), 0 0 40px hsl(var(--primary) / 0.1)",
            }}
          >
            <TrendingUp className="h-7 w-7 text-primary-foreground" />
            <div className="absolute -inset-1 rounded-xl bg-primary/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div className="flex flex-col">
            <span className="text-xl font-extrabold leading-tight gradient-text">
              F3 AI Labs
            </span>
            <span className="text-xs font-medium text-muted-foreground">Parlay AI</span>
          </div>
        </motion.div>

        <nav className="hidden md:flex items-center gap-8">
          {["Builder", "Games", "Analytics"].map((item) => (
            <motion.a
              key={item}
              href={`#${item.toLowerCase()}`}
              className="text-sm font-semibold text-muted-foreground transition-all relative group"
              whileHover={{ color: PRIMARY_NEON }}
            >
              {item}
              <motion.span
                className="absolute -bottom-1 left-0 h-0.5 bg-primary w-0 group-hover:w-full transition-all duration-300"
                initial={{ width: 0 }}
                whileHover={{ width: "100%" }}
              />
            </motion.a>
          ))}
        </nav>

        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="sm"
            className="hidden md:inline-flex border-primary/50 hover:border-primary hover:text-primary"
          >
            Sign In
          </Button>
          <GlowButton size="sm" variant="neon" className="hidden md:inline-flex">
            Get Started
          </GlowButton>
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="border-t md:hidden">
          <div className="container space-y-1 px-4 py-4">
            <a
              href="#builder"
              className="block px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              onClick={() => setMobileMenuOpen(false)}
            >
              Builder
            </a>
            <a
              href="#games"
              className="block px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              onClick={() => setMobileMenuOpen(false)}
            >
              Games
            </a>
            <a
              href="#analytics"
              className="block px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              onClick={() => setMobileMenuOpen(false)}
            >
              Analytics
            </a>
            <div className="flex gap-2 pt-2">
              <Button variant="outline" size="sm" className="flex-1 border-primary/50 hover:border-primary hover:text-primary">
                Sign In
              </Button>
              <GlowButton size="sm" variant="neon" className="flex-1">
                Get Started
              </GlowButton>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}

