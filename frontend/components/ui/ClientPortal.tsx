"use client"

import { useEffect, useState, type ReactNode } from "react"
import { createPortal } from "react-dom"

function getOrCreatePortalContainer(containerId: string): HTMLElement | null {
  if (typeof document === "undefined") return null

  const existing = document.getElementById(containerId)
  if (existing) return existing

  const container = document.createElement("div")
  container.setAttribute("id", containerId)
  document.body.appendChild(container)
  return container
}

export function ClientPortal({
  children,
  containerId = "pg-portal-root",
}: {
  children: ReactNode
  containerId?: string
}) {
  const [container, setContainer] = useState<HTMLElement | null>(null)

  useEffect(() => {
    setContainer(getOrCreatePortalContainer(containerId))
  }, [containerId])

  if (!container) return null
  return createPortal(children, container)
}


