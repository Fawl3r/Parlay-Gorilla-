import { describe, expect, it, vi } from "vitest"

import { BringIntoViewManager } from "@/lib/ui/BringIntoViewManager"

describe("BringIntoViewManager", () => {
  it("does nothing when element is null", () => {
    expect(() => BringIntoViewManager.bringIntoView(null)).not.toThrow()
  })

  it("calls scrollIntoView and focus with provided options", () => {
    const scrollIntoView = vi.fn()
    const focus = vi.fn()

    const element = { scrollIntoView, focus } as unknown as HTMLElement

    BringIntoViewManager.bringIntoView(element, { behavior: "instant", block: "center", inline: "nearest" })

    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: "instant", block: "center", inline: "nearest" })
    expect(focus).toHaveBeenCalledWith({ preventScroll: true })
  })

  it("uses requestAnimationFrame when available", () => {
    const raf = vi.fn((cb: () => void) => cb())
    ;(globalThis as any).window = { requestAnimationFrame: raf }

    const scrollIntoView = vi.fn()
    const focus = vi.fn()
    const element = { scrollIntoView, focus } as unknown as HTMLElement

    BringIntoViewManager.bringIntoView(element, { behavior: "instant", block: "center" })

    expect(raf).toHaveBeenCalledTimes(1)

    delete (globalThis as any).window
  })
})


