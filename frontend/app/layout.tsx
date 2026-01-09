import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
import { Suspense } from 'react'
import './globals.css'
import { ThemeProvider } from '@/components/ThemeProvider'
import { GlobalBackground } from '@/components/GlobalBackground'
import { AuthProvider } from '@/lib/auth-context'
import { SubscriptionProvider } from '@/lib/subscription-context'
import { AffiliatePromoBanner } from '@/components/AffiliatePromoBanner'
import { ReferralTrackerClient } from '@/components/affiliates/ReferralTrackerClient'
import { MobileShell } from '@/components/navigation/MobileShell'
import { VerificationCelebrationProvider } from '@/components/verification/VerificationCelebrationProvider'
import { Toaster } from 'sonner'

const inter = Inter({ subsets: ['latin'] })

function resolveSiteUrl(): string {
  const raw = process.env.NEXT_PUBLIC_SITE_URL || 'https://parlaygorilla.com'
  if (raw.includes('://')) return raw
  return `https://${raw}`
}

const SITE_URL = resolveSiteUrl()

// Rotating preview images - cycles through these based on the date
const PREVIEW_IMAGES = [
  '/images/pgbb2.png', // Baseball gorilla
  '/images/gorilla-basketball.png',
  '/images/gorilla-football.png',
  '/images/gorilla-hockey.png',
  '/images/gorilla-soccer.png',
  '/images/pg baseball.png',
]

/**
 * Selects a preview image based on the current date.
 * The same image will be used throughout the day, then rotate to the next one.
 * This ensures consistency for social media caching while still rotating images.
 * 
 * To change rotation frequency:
 * - Daily (current): Uses dayOfYear
 * - Weekly: Use Math.floor(dayOfYear / 7) instead
 * - Hourly: Use Math.floor(now.getTime() / (1000 * 60 * 60)) instead
 * - Random: Use Math.floor(Math.random() * PREVIEW_IMAGES.length) (not recommended for caching)
 */
function getRotatingPreviewImage(): string {
  // Use the day of the year (1-365/366) to cycle through images
  const now = new Date()
  const startOfYear = new Date(now.getFullYear(), 0, 0)
  const dayOfYear = Math.floor((now.getTime() - startOfYear.getTime()) / (1000 * 60 * 60 * 24))
  
  // Cycle through images based on day of year
  const imageIndex = dayOfYear % PREVIEW_IMAGES.length
  return PREVIEW_IMAGES[imageIndex] || PREVIEW_IMAGES[0]
}

export function generateMetadata(): Metadata {
  const previewImage = getRotatingPreviewImage()
  
  return {
    metadataBase: new URL(SITE_URL),
    title: 'Parlay Gorilla™ – AI Sports Analytics',
    description:
      'AI-assisted sports analytics and informational insights (probability analysis, risk indicators) for building and evaluating parlays. Not a sportsbook. 18+ only.',
    icons: {
      icon: '/images/newlogohead.png',
      shortcut: '/images/newlogohead.png',
      apple: '/images/newlogohead.png',
    },
    verification: {
      google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION,
    },
    openGraph: {
      title: 'Parlay Gorilla™ – AI Sports Analytics',
      description:
        'AI-assisted sports analytics and informational insights (probability analysis, risk indicators) for building and evaluating parlays. Not a sportsbook. 18+ only.',
      url: SITE_URL,
      siteName: 'Parlay Gorilla',
      images: [
        {
          url: previewImage,
          width: 1200,
          height: 630,
          alt: 'Parlay Gorilla - AI Sports Analytics',
        },
      ],
      locale: 'en_US',
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: 'Parlay Gorilla™ – AI Sports Analytics',
      description:
        'AI-assisted sports analytics and informational insights (probability analysis, risk indicators) for building and evaluating parlays. Not a sportsbook. 18+ only.',
      images: [previewImage],
    },
  }
}

// Google AdSense Client ID
const adsenseClientId = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Theme bootstrap (runs before React hydrates). Avoid mutating <body> here to prevent hydration mismatches. */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                // Apply theme
                const theme = localStorage.getItem('theme') || 'dark';
                const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                if (isDark) {
                  document.documentElement.classList.add('dark');
                  document.documentElement.style.backgroundColor = '#0a0a0f';
                } else {
                  document.documentElement.classList.remove('dark');
                  document.documentElement.style.backgroundColor = '#e5e7eb';
                }
              })();
            `,
          }}
        />
        {/* Google AdSense Script - Only load in production with valid client ID */}
        {adsenseClientId && process.env.NODE_ENV === 'production' && (
          <Script
            id="google-adsense"
            async
            src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${adsenseClientId}`}
            crossOrigin="anonymous"
            strategy="afterInteractive"
          />
        )}
      </head>
      <body className={inter.className}>
        <Suspense fallback={null}>
          <ReferralTrackerClient />
        </Suspense>
        <ThemeProvider>
          <GlobalBackground intensity="medium" />
          <AuthProvider>
            <SubscriptionProvider>
              <AffiliatePromoBanner variant="banner" />
              <VerificationCelebrationProvider>
                <MobileShell>{children}</MobileShell>
              </VerificationCelebrationProvider>
              <Toaster closeButton richColors position="top-center" theme="dark" />
            </SubscriptionProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}

