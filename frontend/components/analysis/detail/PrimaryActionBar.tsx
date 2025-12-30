"use client"

import { Bookmark, BookmarkCheck, Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export type PrimaryActionBarProps = {
  onAddToParlay: () => void
  onSave: () => void
  isSaved: boolean
  addDisabled?: boolean
  saveDisabled?: boolean
  className?: string
}

export function PrimaryActionBar({
  onAddToParlay,
  onSave,
  isSaved,
  addDisabled = false,
  saveDisabled = false,
  className,
}: PrimaryActionBarProps) {
  return (
    <div
      className={cn(
        // Keep above the global mobile bottom tabs (also z-50).
        "fixed inset-x-0 z-[60] md:hidden",
        "border-t border-white/10 bg-black/70 backdrop-blur-xl",
        className
      )}
      style={{
        // Float above the global mobile bottom navigation bar.
        bottom: "calc(env(safe-area-inset-bottom) + 72px)",
        paddingBottom: "12px",
      }}
      aria-label="Primary actions"
    >
      <div className="container mx-auto max-w-6xl px-4 pt-3">
        <div className="grid grid-cols-2 gap-3">
          <Button onClick={onAddToParlay} disabled={addDisabled} className="h-11 font-extrabold">
            <Plus className="h-4 w-4 mr-2" />
            Add to Parlay
          </Button>
          <Button onClick={onSave} disabled={saveDisabled} variant="outline" className="h-11 font-extrabold">
            {isSaved ? <BookmarkCheck className="h-4 w-4 mr-2" /> : <Bookmark className="h-4 w-4 mr-2" />}
            {isSaved ? "Saved" : "Save"}
          </Button>
        </div>
      </div>
    </div>
  )
}


