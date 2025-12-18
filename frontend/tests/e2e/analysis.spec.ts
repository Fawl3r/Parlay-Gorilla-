import { test, expect } from "@playwright/test";
import { buildAnalysisUrl } from "../../lib/routing/AnalysisUrlBuilder";

test.describe("Analysis endpoints", () => {
  test("Upcoming analyses endpoint returns a list (or empty) without server errors", async ({ request }) => {
    const backendUrl = process.env.PG_BACKEND_URL || "http://localhost:8000";

    const res = await request.get(`${backendUrl}/api/analysis/nfl/upcoming?limit=5`, {
      timeout: 30_000,
    });

    expect(res.status()).toBeLessThan(500);

    if (res.ok()) {
      const items = await res.json();
      expect(Array.isArray(items)).toBeTruthy();
    }
  });

  test("Analysis detail returns analysis_content and model_win_probability (refresh-safe)", async ({ request }) => {
    const backendUrl = process.env.PG_BACKEND_URL || "http://localhost:8000";

    const listRes = await request.get(`${backendUrl}/api/analysis/nfl/upcoming?limit=5`, {
      timeout: 30_000,
    });
    expect(listRes.status()).toBeLessThan(500);
    test.skip(!listRes.ok(), "Analysis list endpoint not available");

    const items = (await listRes.json()) as any[];
    test.skip(!Array.isArray(items) || items.length === 0, "No analyses present in DB");

    const slug = String(items[0]?.slug || "");
    test.skip(!slug, "No slug returned from list endpoint");

    const slugParam = slug.toLowerCase().startsWith("nfl/") ? slug.slice(4) : slug;

    const detailRes = await request.get(`${backendUrl}/api/analysis/nfl/${slugParam}`, {
      timeout: 30_000,
    });
    expect(detailRes.status()).toBeLessThan(500);
    test.skip(!detailRes.ok(), "Analysis detail endpoint not available");

    const analysis = await detailRes.json();
    expect(analysis).toHaveProperty("analysis_content");
    expect(analysis.analysis_content).toHaveProperty("model_win_probability");
    expect(typeof analysis.analysis_content.model_win_probability.home_win_prob).toBe("number");
    expect(typeof analysis.analysis_content.model_win_probability.away_win_prob).toBe("number");

    // Core content should never be the placeholder.
    expect(String(analysis.analysis_content.opening_summary || "").toLowerCase()).not.toContain(
      "analysis is being prepared"
    );
    expect(analysis.analysis_content).toHaveProperty("ats_trends");
    expect(analysis.analysis_content).toHaveProperty("totals_trends");
    expect(String(analysis.analysis_content.ats_trends?.analysis || "")).not.toBe("");
    expect(String(analysis.analysis_content.totals_trends?.analysis || "")).not.toBe("");
    expect(String(analysis.analysis_content.ai_spread_pick?.pick || "")).not.toBe("");
    expect(String(analysis.analysis_content.ai_total_pick?.pick || "")).not.toBe("");

    // Refresh should never hang or crash.
    const refreshRes = await request.get(`${backendUrl}/api/analysis/nfl/${slugParam}?refresh=true`, {
      timeout: 30_000,
    });
    expect(refreshRes.status()).toBeLessThan(500);

    if (refreshRes.ok()) {
      const refreshed = await refreshRes.json();
      expect(String(refreshed.analysis_content?.opening_summary || "").toLowerCase()).not.toContain(
        "analysis is being prepared"
      );
      expect(String(refreshed.analysis_content?.ats_trends?.analysis || "")).not.toBe("");
      expect(String(refreshed.analysis_content?.totals_trends?.analysis || "")).not.toBe("");
    }
  });

  test("NFL Rams @ Seahawks slug resolves when the matchup is present in games", async ({ request }) => {
    const backendUrl =
      process.env.PG_BACKEND_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      process.env.BACKEND_URL ||
      "http://localhost:8000";

    const gamesRes = await request.get(`${backendUrl}/api/sports/nfl/games`, { timeout: 30_000 });
    expect(gamesRes.status()).toBeLessThan(500);
    test.skip(!gamesRes.ok(), "Games endpoint not available");

    const games = (await gamesRes.json()) as Array<{
      away_team?: string
      home_team?: string
      start_time?: string
      week?: number | null
    }>;

    const target = games.find(
      (g) =>
        (g.away_team || "").toLowerCase() === "los angeles rams" &&
        (g.home_team || "").toLowerCase() === "seattle seahawks"
    );

    test.skip(!target, "Target Rams/Seahawks matchup not in current games window");
    test.skip(!target.start_time, "Target game missing start_time");

    const fullPath = buildAnalysisUrl(
      "nfl",
      target.away_team || "",
      target.home_team || "",
      target.start_time,
      target.week ?? null
    );

    // buildAnalysisUrl returns `/analysis/nfl/...`
    const slugParam = fullPath.replace(/^\/analysis\/nfl\//, "");

    const detailRes = await request.get(`${backendUrl}/api/analysis/nfl/${slugParam}`, {
      timeout: 30_000,
    });

    // Must not 500; and if the game exists, should not be a 404 (on-demand generation/placeholder allowed).
    expect(detailRes.status()).toBeLessThan(500);
    expect(detailRes.status()).not.toBe(404);
  });
});


