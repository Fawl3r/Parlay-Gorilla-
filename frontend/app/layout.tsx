import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from '@/components/ThemeProvider'
import { ParlayGorillaBackground } from '@/components/ParlayGorillaBackground'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'F3 Parlay AI – Predictive Parlay Engine',
  description: 'AI-powered sports betting assistant that generates 1–20 leg parlays with win probabilities and detailed explanations',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <ParlayGorillaBackground intensity="medium" />
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  )
}

