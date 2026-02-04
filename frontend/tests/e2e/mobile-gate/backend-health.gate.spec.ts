/**
 * @gate Backend health + odds availability probe.
 * Fails if /health is down or odds provider returned 0 games (games_with_odds).
 */
import { test, expect } from "@playwright/test";
import { getBackendUrl } from "../../mobile/helpers/auth";

test.describe("Mobile Gate — Backend health + odds @gate", () => {
  test("Backend health returns 200 and games/odds availability", async ({ request }) => {
    const base = getBackendUrl();

    await test.step("GET /health", async () => {
      const res = await request.get(`${base}/health`, { timeout: 15_000 });
      expect(res.status(), "Backend /health must return 200").toBe(200);
      const body = (await res.json()) as { status?: string };
      expect(
        body.status === "healthy" || body.status === "degraded",
        "Backend health status should be healthy or degraded",
      ).toBe(true);
    });

    await test.step("GET /health/games — at least one sport with odds", async () => {
      const res = await request.get(`${base}/health/games`, { timeout: 15_000 });
      expect(res.status(), "Backend /health/games must return 200").toBe(200);
      const body = (await res.json()) as {
        games?: {
          with_markets_by_sport?: Record<string, number>;
          total_by_sport?: Record<string, number>;
        };
      };
      const withMarkets = body.games?.with_markets_by_sport ?? {};
      const totalWithOdds = Object.values(withMarkets).reduce((a, b) => a + b, 0);
      expect(
        totalWithOdds,
        "Odds provider returned 0 games with markets. Check provider config, rate limit, and sport season logic (games_with_odds=0).",
      ).toBeGreaterThan(0);
    });
  });
});
