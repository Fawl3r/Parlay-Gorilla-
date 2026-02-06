import { beforeEach, describe, expect, it, vi } from "vitest"

import {
  loadSlip,
  saveSlip,
  clearSlip,
  filterValidPicks,
  type PersistedCustomBuilderSlip,
} from "@/lib/custom-parlay/customBuilderPersistence"
import type { SelectedPick } from "@/components/custom-parlay/types"
import type { GameResponse } from "@/lib/api"

let storage: Record<string, string> = {}

beforeEach(() => {
  storage = {}
  vi.stubGlobal("window", {})
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => storage[key] ?? null,
    setItem: (key: string, value: string) => {
      storage[key] = value
    },
    removeItem: (key: string) => {
      delete storage[key]
    },
  })
})

function makePick(overrides: Partial<SelectedPick> = {}): SelectedPick {
  return {
    game_id: "g1",
    market_type: "h2h",
    pick: "Chiefs",
    gameDisplay: "Bills @ Chiefs",
    pickDisplay: "Chiefs ML",
    homeTeam: "Chiefs",
    awayTeam: "Bills",
    sport: "nfl",
    oddsDisplay: "+120",
    ...overrides,
  }
}

function makeGame(overrides: Partial<GameResponse> = {}): GameResponse {
  return {
    id: "g1",
    external_game_id: "ext1",
    sport: "nfl",
    home_team: "Chiefs",
    away_team: "Bills",
    start_time: "2025-02-01T18:30:00Z",
    status: "scheduled",
    markets: [
      { id: "m1", market_type: "h2h", book: "fanduel", odds: [{ id: "o1", outcome: "Chiefs", price: "+120", decimal_price: 2.2, implied_prob: 0.45, created_at: "" }] },
    ],
    ...overrides,
  }
}

describe("customBuilderPersistence", () => {
  describe("saveSlip / loadSlip roundtrip", () => {
    it("saves and loads slip for user", () => {
      const slip: PersistedCustomBuilderSlip = {
        v: 1,
        savedAt: Date.now(),
        selectedSport: "nfl",
        picks: [makePick()],
      }
      saveSlip("user-1", slip)
      const loaded = loadSlip("user-1")
      expect(loaded).not.toBeNull()
      expect(loaded?.selectedSport).toBe("nfl")
      expect(loaded?.picks).toHaveLength(1)
      expect(loaded?.picks[0].game_id).toBe("g1")
    })

    it("saves and loads slip for anon", () => {
      const slip: PersistedCustomBuilderSlip = {
        v: 1,
        savedAt: Date.now(),
        selectedSport: "nba",
        picks: [],
      }
      saveSlip(null, slip)
      const loaded = loadSlip(null)
      expect(loaded).not.toBeNull()
      expect(loaded?.selectedSport).toBe("nba")
    })
  })

  describe("TTL", () => {
    it("returns null when slip is older than 12h", () => {
      const key = "pg_custom_builder_slip:user-1"
      const expired = {
        v: 1,
        savedAt: Date.now() - (13 * 60 * 60 * 1000),
        selectedSport: "nfl",
        picks: [makePick()],
      }
      storage[key] = JSON.stringify(expired)
      const loaded = loadSlip("user-1")
      expect(loaded).toBeNull()
    })
  })

  describe("clearSlip", () => {
    it("removes persisted slip", () => {
      const slip: PersistedCustomBuilderSlip = {
        v: 1,
        savedAt: Date.now(),
        selectedSport: "nfl",
        picks: [makePick()],
      }
      saveSlip("user-1", slip)
      expect(loadSlip("user-1")).not.toBeNull()
      clearSlip("user-1")
      expect(loadSlip("user-1")).toBeNull()
    })
  })

  describe("filterValidPicks", () => {
    it("drops picks for missing games", () => {
      const picks = [makePick({ game_id: "g1" }), makePick({ game_id: "g99", gameDisplay: "Other", pickDisplay: "Other ML", homeTeam: "A", awayTeam: "B" })]
      const games = [makeGame({ id: "g1" })]
      const result = filterValidPicks(picks, games)
      expect(result).toHaveLength(1)
      expect(result[0].game_id).toBe("g1")
    })

    it("keeps picks for existing games with matching market", () => {
      const picks = [makePick({ game_id: "g1", market_type: "h2h", pick: "Chiefs" })]
      const games = [makeGame({ id: "g1", markets: [{ id: "m1", market_type: "h2h", book: "fd", odds: [{ id: "o1", outcome: "Chiefs", price: "+120", decimal_price: 2.2, implied_prob: 0.45, created_at: "" }] }] })]
      const result = filterValidPicks(picks, games)
      expect(result).toHaveLength(1)
    })

    it("drops pick when market_type not on game", () => {
      const picks = [makePick({ game_id: "g1", market_type: "player_props" })]
      const games = [makeGame({ id: "g1", markets: [{ id: "m1", market_type: "h2h", book: "fd", odds: [] }] })]
      const result = filterValidPicks(picks, games)
      expect(result).toHaveLength(0)
    })

    it("keeps picks from other sports when filtering against single-sport games list", () => {
      const nflPick = makePick({ game_id: "g-nfl", sport: "nfl", gameDisplay: "Bills @ Chiefs", pickDisplay: "Chiefs ML", homeTeam: "Chiefs", awayTeam: "Bills" })
      const nbaPick = makePick({
        game_id: "g-nba",
        sport: "nba",
        pick: "LAL",
        gameDisplay: "LAL @ BOS",
        pickDisplay: "LAL ML",
        homeTeam: "BOS",
        awayTeam: "LAL",
      })
      const picks = [nflPick, nbaPick]
      const games = [
        makeGame({
          id: "g-nba",
          sport: "nba",
          home_team: "BOS",
          away_team: "LAL",
          markets: [{ id: "m2", market_type: "h2h", book: "fd", odds: [{ id: "o2", outcome: "LAL", price: "+150", decimal_price: 2.5, implied_prob: 0.4, created_at: "" }] }],
        }),
      ]
      const result = filterValidPicks(picks, games)
      expect(result).toHaveLength(2)
      expect(result[0].sport).toBe("nfl")
      expect(result[1].sport).toBe("nba")
    })
  })
})
