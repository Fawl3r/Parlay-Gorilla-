"use client"

import Link from "next/link"
import Image from "next/image"

export function Footer() {
  return (
    <footer className="border-t border-white/10 bg-[#0a0a0f] py-16">
      <div className="container px-4">
        <div className="grid gap-8 md:grid-cols-4">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="relative flex h-8 w-8 items-center justify-center rounded-lg overflow-hidden" style={{
                boxShadow: "0 2px 10px rgba(139, 92, 246, 0.4), 0 0 20px rgba(59, 130, 246, 0.3)",
              }}>
                <Image
                  src="/logoo.png"
                  alt="Parlay Gorilla Logo"
                  width={32}
                  height={32}
                  className="object-contain"
                />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-bold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-green-400">
                  Parlay Gorilla
                </span>
                <span className="text-[10px] text-gray-500 tracking-wide">AI PARLAY ENGINE</span>
              </div>
            </div>
            <p className="text-sm text-gray-500 leading-relaxed">
              AI-powered parlay engine for intelligent sports betting decisions.
            </p>
          </div>

          <div>
            <h3 className="mb-4 text-sm font-semibold text-white">Product</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/app" className="text-gray-500 hover:text-emerald-400 transition-colors">
                  AI Parlay Engine
                </Link>
              </li>
              <li>
                <Link href="/app" className="text-gray-500 hover:text-emerald-400 transition-colors">
                  AI Parlay Builder
                </Link>
              </li>
              <li>
                <Link href="/analytics" className="text-gray-500 hover:text-emerald-400 transition-colors">
                  Analytics
                </Link>
              </li>
              <li>
                <Link href="/analysis" className="text-gray-500 hover:text-emerald-400 transition-colors">
                  Game Analysis
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="mb-4 text-sm font-semibold text-white">Resources</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/docs" className="text-gray-500 hover:text-emerald-400 transition-colors">
                  Documentation
                </Link>
              </li>
              <li>
                <Link href="/support" className="text-gray-500 hover:text-emerald-400 transition-colors">
                  Support
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="mb-4 text-sm font-semibold text-white">Legal</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/terms" className="text-gray-500 hover:text-emerald-400 transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="text-gray-500 hover:text-emerald-400 transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/responsible-gaming" className="text-gray-500 hover:text-emerald-400 transition-colors">
                  Responsible Gaming
                </Link>
              </li>
              <li>
                <Link href="/admin/login" className="text-gray-500 hover:text-emerald-400 transition-colors">
                  Admin Login
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-white/10 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-gray-600">
            © {new Date().getFullYear()} Parlay Gorilla. All rights reserved.
          </p>
          <p className="text-xs text-gray-700">
            For entertainment purposes only. Please gamble responsibly.
          </p>
        </div>
      </div>
    </footer>
  )
}
