"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useEffect, useMemo, useRef, useState } from "react"

import { useSubscription } from "@/lib/subscription-context"
import { cn } from "@/lib/utils"

export type AvatarMenuDropdownProps = {
  userEmail: string | null
  onSignOut: () => Promise<void>
  className?: string
}

function formatShortMonthDay(date: Date): string {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  return `${months[date.getMonth()]} ${date.getDate()}`
}

function derivePlanLabel(planCode: string | null, isLifetime: boolean, isPremium: boolean): string {
  if (isLifetime) return "Lifetime"
  const code = String(planCode || "").toLowerCase().trim()
  if (code.includes("elite")) return "Elite"
  if (code.includes("standard") || code.includes("pro")) return "Pro"
  if (isPremium) return "Pro"
  return "Free"
}

export function AvatarMenuDropdown({ userEmail, onSignOut, className }: AvatarMenuDropdownProps) {
  const router = useRouter()
  const pathname = usePathname() || "/"
  const { status, isPremium } = useSubscription()

  const isAuthed = Boolean(userEmail)
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement | null>(null)

  const planLabel = useMemo(() => {
    return derivePlanLabel(status?.plan_code ?? null, Boolean(status?.is_lifetime), Boolean(isPremium))
  }, [isPremium, status?.is_lifetime, status?.plan_code])

  const renewalLabel = useMemo(() => {
    if (!isAuthed) return null
    if (status?.is_lifetime) return null
    const raw = status?.subscription_end
    if (!raw) return null
    const dt = new Date(raw)
    if (!Number.isFinite(dt.getTime())) return null
    return `Renews ${formatShortMonthDay(dt)}`
  }, [isAuthed, status?.is_lifetime, status?.subscription_end])

  useEffect(() => {
    function onDocMouseDown(evt: MouseEvent) {
      const el = rootRef.current
      if (!el) return
      if (evt.target instanceof Node && !el.contains(evt.target)) setOpen(false)
    }
    document.addEventListener("mousedown", onDocMouseDown)
    return () => document.removeEventListener("mousedown", onDocMouseDown)
  }, [])

  const initials = useMemo(() => {
    const email = String(userEmail || "").trim()
    if (!email) return "A"
    const first = email[0]?.toUpperCase() || "A"
    return first
  }, [userEmail])

  const buttonLabel = isAuthed ? "Account menu" : "Sign in menu"

  return (
    <div ref={rootRef} className={cn("relative", className)} data-testid="avatar-menu">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "inline-flex items-center justify-center",
          "h-10 w-10 rounded-full border border-white/10 bg-white/5",
          "text-white/80 font-black hover:bg-white/10 transition-colors"
        )}
        aria-label={buttonLabel}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        {initials}
      </button>

      {open ? (
        <div
          role="menu"
          aria-label="Account menu"
          className={cn(
            "absolute right-0 mt-2 w-56 overflow-hidden rounded-xl border border-white/10",
            "bg-black/80 backdrop-blur-xl shadow-xl"
          )}
        >
          <div className="py-2">
            {isAuthed ? (
              <>
                <MenuLink href="/profile" label="Profile" currentPath={pathname} onClick={() => setOpen(false)} />
                <MenuLink href="/usage" label="Usage & Performance" currentPath={pathname} onClick={() => setOpen(false)} />
                <MenuLink href="/leaderboards" label="Leaderboards" currentPath={pathname} onClick={() => setOpen(false)} />
                <MenuLink href="/billing" label="Plan & Billing" currentPath={pathname} onClick={() => setOpen(false)} />
                <MenuLink href="/tutorial" label="Help & Tutorial" currentPath={pathname} onClick={() => setOpen(false)} />

                <div className="my-1 border-t border-white/10" />

                <button
                  type="button"
                  role="menuitem"
                  onClick={async () => {
                    setOpen(false)
                    await onSignOut()
                    router.push("/auth/login")
                  }}
                  className={cn(
                    "w-full text-left px-4 py-2.5 text-sm font-semibold",
                    "text-white/70 hover:text-white hover:bg-white/10 transition-colors"
                  )}
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <MenuLink href="/auth/login" label="Sign in" currentPath={pathname} onClick={() => setOpen(false)} />
                <MenuLink href="/auth/signup" label="Create account" currentPath={pathname} onClick={() => setOpen(false)} />
              </>
            )}
          </div>

          {isAuthed ? (
            <div className="border-t border-white/10 px-4 py-2 text-[11px] text-white/45">
              Plan: {planLabel}
              {renewalLabel ? ` — ${renewalLabel}` : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

function MenuLink({
  href,
  label,
  currentPath,
  onClick,
}: {
  href: string
  label: string
  currentPath: string
  onClick: () => void
}) {
  const active = currentPath === href || currentPath.startsWith(`${href}/`)
  return (
    <Link
      href={href}
      role="menuitem"
      aria-current={active ? "page" : undefined}
      onClick={onClick}
      className={cn(
        "block px-4 py-2.5 text-sm font-semibold transition-colors",
        active ? "text-emerald-300" : "text-white/70 hover:text-white hover:bg-white/10"
      )}
    >
      {label}
    </Link>
  )
}

export default AvatarMenuDropdown


