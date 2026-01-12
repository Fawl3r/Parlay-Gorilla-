"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

import { useAuth } from "@/lib/auth-context"
import { PrimaryNavManager } from "@/lib/navigation/PrimaryNavManager"
import { cn } from "@/lib/utils"

export function PrimaryNav() {
  const pathname = usePathname() || "/"
  const { user } = useAuth()

  const manager = new PrimaryNavManager()
  const items = manager.getItems({ isAuthed: Boolean(user) })

  return (
    <nav className="hidden md:flex items-center gap-2" aria-label="Primary navigation">
      {items.map((item) => {
        const active = item.isActive(pathname)
        return (
          <Link
            key={item.id}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "rounded-lg px-3 py-2 text-sm font-semibold transition-colors",
              "min-h-[44px] inline-flex items-center",
              active ? "text-emerald-300" : "text-white/70 hover:text-white"
            )}
          >
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}

export default PrimaryNav





