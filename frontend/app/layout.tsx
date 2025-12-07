import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
import './globals.css'
import { ThemeProvider } from '@/components/ThemeProvider'
import { GlobalBackground } from '@/components/GlobalBackground'
import { AuthProvider } from '@/lib/auth-context'
import { SubscriptionProvider } from '@/lib/subscription-context'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Parlay Gorilla – Predictive Parlay Engine',
  description: 'AI-powered sports betting assistant that generates 1–20 leg parlays with win probabilities and detailed explanations',
  icons: {
    icon: '/logoo.png',
    shortcut: '/logoo.png',
    apple: '/logoo.png',
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
        {/* Prevent flash of light content - apply dark mode immediately */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
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
        <ThemeProvider>
          <GlobalBackground showGorilla={true} intensity="medium" />
          <AuthProvider>
            <SubscriptionProvider>
              {children}
            </SubscriptionProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}

