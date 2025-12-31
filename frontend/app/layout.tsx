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
import { Toaster } from 'sonner'

const inter = Inter({ subsets: ['latin'] })

function resolveSiteUrl(): string {
  const raw = process.env.NEXT_PUBLIC_SITE_URL || 'https://parlaygorilla.com'
  if (raw.includes('://')) return raw
  return `https://${raw}`
}

const SITE_URL = resolveSiteUrl()

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: 'Parlay Gorilla™ – AI Sports Analytics',
  description:
    'AI-assisted sports analytics and informational insights (probability analysis, risk indicators) for building and evaluating parlays. Not a sportsbook. 21+ only.',
  icons: {
    icon: '/images/newlogohead.png',
    shortcut: '/images/newlogohead.png',
    apple: '/images/newlogohead.png',
  },
  verification: {
    google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION,
  },
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
        {/* LemonSqueezy Lemon.js (affiliate tracking + checkout helpers) */}
        <Script id="lemonsqueezy-lemonjs" src="https://app.lemonsqueezy.com/js/lemon.js" strategy="afterInteractive" />
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
              <MobileShell>{children}</MobileShell>
              <Toaster closeButton richColors position="top-center" theme="dark" />
            </SubscriptionProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}

