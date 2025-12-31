"use client"

import { useRouter } from "next/navigation"

import { cn } from "@/lib/utils"

export type GenerateButtonProps = {
  onGenerate?: () => void
  className?: string
}

export function GenerateButton({ onGenerate, className }: GenerateButtonProps) {
  const router = useRouter()

  const handleClick = () => {
    if (onGenerate) {
      onGenerate()
    } else {
      router.push("/build")
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        "inline-flex items-center justify-center rounded-xl font-black",
        "bg-emerald-500 text-black hover:bg-emerald-400 transition-colors",
        "min-h-[44px] px-4 py-2 text-sm",
        className
      )}
      aria-label="Generate"
    >
      + Generate
    </button>
  )
}

export default GenerateButton


