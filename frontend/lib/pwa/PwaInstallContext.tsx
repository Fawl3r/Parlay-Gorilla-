'use client'

import { createContext, useContext, type ReactNode } from 'react'
import { usePwaInstall, type UsePwaInstallReturn } from './usePwaInstall'

const PwaInstallContext = createContext<UsePwaInstallReturn | undefined>(undefined)

export function PwaInstallProvider({ children }: { children: ReactNode }) {
  const value = usePwaInstall()
  return (
    <PwaInstallContext.Provider value={value}>
      {children}
    </PwaInstallContext.Provider>
  )
}

export function usePwaInstallContext(): UsePwaInstallReturn {
  const ctx = useContext(PwaInstallContext)
  if (ctx === undefined) {
    throw new Error('usePwaInstallContext must be used within PwaInstallProvider')
  }
  return ctx
}

/** Use when you only need to nudge the install CTA (e.g. on value moments). */
export function usePwaInstallNudge(): { nudgeInstallCta: () => void } {
  const { nudgeInstallCta } = usePwaInstallContext()
  return { nudgeInstallCta }
}
