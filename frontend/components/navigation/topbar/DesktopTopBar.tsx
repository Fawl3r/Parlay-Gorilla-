"use client"

import Link from "next/link"

import { ParlayGorillaLogo } from "@/components/ParlayGorillaLogo"
import { StatusIndicator } from "@/components/ui/status-indicator"
import { cn } from "@/lib/utils"

import { AvatarMenuDropdown } from "./AvatarMenuDropdown"
import { PrimaryNav } from "./PrimaryNav"

export type DesktopTopBarProps = {
  homeHref: string
  userEmail: string | null
  onSignOut: () => Promise<void>
  onGenerate?: () => void
  className?: string
  hideNav?: boolean
  showStatusIndicator?: boolean
}

export function DesktopTopBar({
  homeHref,
  userEmail,
  onSignOut,
  onGenerate,
  className,
  hideNav = false,
  showStatusIndicator = false,
}: DesktopTopBarProps) {
  return (
    <div className={cn("hidden md:flex h-16 items-center justify-between gap-4 flex-1", className)}>
      <div className="flex items-center gap-4 min-w-0">
        <Link href={homeHref} className="shrink-0 flex items-center gap-2" aria-label="Home">
          <ParlayGorillaLogo size="sm" />
        </Link>
        {showStatusIndicator && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10">
            <StatusIndicator type="success" pulse size="sm" />
            <span className="text-xs font-medium text-white/80">Gorilla AI Online</span>
          </div>
        )}
        {!hideNav && <PrimaryNav />}
      </div>

      <div className="flex items-center gap-3">
        <AvatarMenuDropdown userEmail={userEmail} onSignOut={onSignOut} />
      </div>
    </div>
  )
}

export default DesktopTopBar




