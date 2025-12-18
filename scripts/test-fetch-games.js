/**
 * Quick test script to fetch games for a sport and check a specific date.
 *
 * Usage:
 *   node scripts/test-fetch-games.js nba 2025-12-08 http://localhost:8000
 *
 * Defaults:
 *   sport: nba
 *   date: today (local)
 *   apiBase: http://localhost:8000
 */

const sport = process.argv[2] || "nba";
const dateArg = process.argv[3] || "today";
const apiBase = process.argv[4] || "http://localhost:8000";

function getTargetDate(dateStr) {
  const today = new Date();
  if (dateStr === "today") return today;
  if (dateStr === "tomorrow") {
    const t = new Date(today);
    t.setDate(t.getDate() + 1);
    return t;
  }
  const [y, m, d] = dateStr.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

function isOnDate(startTime, targetDate) {
  const dt = new Date(startTime);
  return (
    dt.getUTCFullYear() === targetDate.getUTCFullYear() &&
    dt.getUTCMonth() === targetDate.getUTCMonth() &&
    dt.getUTCDate() === targetDate.getUTCDate()
  );
}

async function main() {
  const targetDate = getTargetDate(dateArg);
  const url = `${apiBase}/api/sports/${sport}/games?refresh=true`;
  console.log(`Fetching ${sport.toUpperCase()} games from ${url} ...`);

  const res = await fetch(url, { timeout: 30000 });
  if (!res.ok) {
    console.error(`Request failed: ${res.status} ${res.statusText}`);
    const text = await res.text();
    console.error(text);
    process.exit(1);
  }

  const games = await res.json();
  console.log(`Total games returned: ${games.length}\n`);

  // Show date distribution
  const dateMap = new Map();
  games.forEach((g) => {
    const dt = new Date(g.start_time);
    const dateStr = dt.toISOString().slice(0, 10);
    if (!dateMap.has(dateStr)) {
      dateMap.set(dateStr, []);
    }
    dateMap.get(dateStr).push(g);
  });

  console.log("Games by date:");
  Array.from(dateMap.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .forEach(([date, gamesOnDate]) => {
      console.log(`  ${date}: ${gamesOnDate.length} games`);
    });

  const onDate = games.filter((g) => isOnDate(g.start_time, targetDate));
  console.log(
    `\nGames on ${targetDate.toISOString().slice(0, 10)}: ${onDate.length}`
  );

  if (onDate.length > 0) {
    onDate
      .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
      .forEach((g, idx) => {
        console.log(
          `${idx + 1}. ${g.away_team} @ ${g.home_team} @ ${g.start_time} (status: ${g.status})`
        );
      });
  } else {
    console.log("\nNo games found for this date. Showing first 5 games for reference:");
    games
      .slice(0, 5)
      .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
      .forEach((g, idx) => {
        const dt = new Date(g.start_time);
        console.log(
          `${idx + 1}. ${g.away_team} @ ${g.home_team} @ ${g.start_time} (date: ${dt.toISOString().slice(0, 10)})`
        );
      });
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

