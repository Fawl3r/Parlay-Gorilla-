"use client"

import { usePathname } from "next/navigation"
import type { ReactNode } from "react"

import { useAuth } from "@/lib/auth-context"
import { cn } from "@/lib/utils"
import { MobileBottomTabs } from "./MobileBottomTabs"
import { GorillaBotWidget } from "@/components/gorilla-bot/GorillaBotWidget"

type Props = {
  children: ReactNode
}

const TAB_ROUTE_PREFIXES = ["/app", "/build", "/analysis", "/analytics", "/profile"]

function shouldShowTabs(pathname: string) {
  const p = (pathname || "/").toLowerCase()
  return TAB_ROUTE_PREFIXES.some((prefix) => p === prefix || p.startsWith(`${prefix}/`))
}

export function MobileShell({ children }: Props) {
  const pathname = usePathname() || "/"
  const { user } = useAuth()

  const showTabs = Boolean(user) && shouldShowTabs(pathname)
  const showGorillaBot = Boolean(user) && shouldShowTabs(pathname)

  return (
    <>
      <div
        className={cn(
          showTabs && "pb-[calc(env(safe-area-inset-bottom,0px)+78px)]"
        )}
      >
        {children}
      </div>
      {showTabs ? <MobileBottomTabs /> : null}
      {showGorillaBot ? <GorillaBotWidget /> : null}
    </>
  )
}

export default MobileShell


