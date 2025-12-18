#!/usr/bin/env node

/**
 * Lightweight perf/cache smoke:
 * - Calls games, analysis upcoming, and parlay suggest twice to observe cache warm vs hot.
 */

const backend = process.env.PG_BACKEND_URL || "http://localhost:8000";
const token = process.env.PG_AUTH_TOKEN || "";

async function timed(name, fn) {
  const start = performance.now();
  const res = await fn();
  const ms = (performance.now() - start).toFixed(1);
  console.log(`${name}: ${ms} ms (status ${res.status})`);
  return res;
}

async function main() {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  // Games
  await timed("games first", () => fetch(`${backend}/api/games/sports/nfl/games`, { headers }));
  await timed("games second (cache)", () => fetch(`${backend}/api/games/sports/nfl/games`, { headers }));

  // Analysis list
  await timed("analysis first", () => fetch(`${backend}/api/analysis/nfl/upcoming`, { headers }));
  await timed("analysis second (cache)", () => fetch(`${backend}/api/analysis/nfl/upcoming`, { headers }));

  // Parlay suggest (requires auth)
  if (token) {
    await timed("parlay suggest first", () =>
      fetch(`${backend}/api/parlay/suggest`, {
        method: "POST",
        headers,
        body: JSON.stringify({ num_legs: 3, risk_profile: "balanced", sports: ["NFL"] }),
      })
    );
    await timed("parlay suggest second (cache)", () =>
      fetch(`${backend}/api/parlay/suggest`, {
        method: "POST",
        headers,
        body: JSON.stringify({ num_legs: 3, risk_profile: "balanced", sports: ["NFL"] }),
      })
    );
  } else {
    console.log("Skip parlay suggest (set PG_AUTH_TOKEN to include)");
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});


