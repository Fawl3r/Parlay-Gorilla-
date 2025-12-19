"use client"

import { useEffect, useRef } from "react"

import type { TripleParlayResponse } from "@/lib/api"
import { BringIntoViewManager } from "@/lib/ui/BringIntoViewManager"

import { TripleParlayDisplay } from "@/components/TripleParlayDisplay"

export function TripleParlayResult({ data }: { data: TripleParlayResponse }) {
  const rootRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    BringIntoViewManager.bringIntoView(rootRef.current, { behavior: "smooth", block: "start" })
  }, [data])

  return (
    <div ref={rootRef} tabIndex={-1}>
      <TripleParlayDisplay data={data} />
    </div>
  )
}


