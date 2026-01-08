import { describe, expect, it } from "vitest"

import { VerificationCelebrationRegistry, type KeyValueStorage } from "@/lib/verification/VerificationCelebrationRegistry"

class MemoryStorage implements KeyValueStorage {
  private readonly map = new Map<string, string>()

  getItem(key: string): string | null {
    return this.map.get(key) ?? null
  }

  setItem(key: string, value: string): void {
    this.map.set(key, value)
  }
}

describe("VerificationCelebrationRegistry", () => {
  it("persists marked ids and restores them", () => {
    const storage = new MemoryStorage()
    const a = new VerificationCelebrationRegistry(storage, { storageKey: "t", maxEntries: 50 })

    expect(a.has("r1")).toBe(false)
    a.mark("r1")
    a.mark("r2")
    expect(a.has("r1")).toBe(true)
    expect(a.snapshot().sort()).toEqual(["r1", "r2"])

    const b = new VerificationCelebrationRegistry(storage, { storageKey: "t", maxEntries: 50 })
    expect(b.has("r1")).toBe(true)
    expect(b.has("r2")).toBe(true)
  })

  it("caps stored entries to maxEntries", () => {
    const storage = new MemoryStorage()
    const reg = new VerificationCelebrationRegistry(storage, { storageKey: "t2", maxEntries: 10 })
    for (let i = 0; i < 25; i++) reg.mark(`r-${i}`)

    const raw = storage.getItem("t2")
    expect(raw).toBeTruthy()
    const parsed = JSON.parse(raw || "[]")
    expect(Array.isArray(parsed)).toBe(true)
    expect(parsed.length).toBeLessThanOrEqual(10)
  })
})


