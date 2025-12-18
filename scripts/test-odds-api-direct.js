/**
 * Test script to directly query The Odds API and see what games it returns.
 * This bypasses our backend to see the raw API response.
 * 
 * Usage:
 *   node scripts/test-odds-api-direct.js nba
 * 
 * Requires THE_ODDS_API_KEY environment variable or .env file
 */

const sport = process.argv[2] || "nba";
const fs = require("fs");
const path = require("path");

// Load .env file if it exists
const envPath = path.join(__dirname, "..", "backend", ".env");
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, "utf8");
  envContent.split("\n").forEach((line) => {
    const match = line.match(/^([^#=]+)=(.*)$/);
    if (match) {
      const key = match[1].trim();
      const value = match[2].trim().replace(/^["']|["']$/g, "");
      if (!process.env[key]) {
        process.env[key] = value;
      }
    }
  });
}

const API_KEY = process.env.THE_ODDS_API_KEY;
if (!API_KEY) {
  console.error("Error: THE_ODDS_API_KEY not found in environment or .env file");
  process.exit(1);
}

const SPORT_KEYS = {
  nba: "basketball_nba",
  nhl: "icehockey_nhl",
  nfl: "americanfootball_nfl",
  mlb: "baseball_mlb",
};

const sportKey = SPORT_KEYS[sport] || sport;

async function main() {
  const url = `https://api.the-odds-api.com/v4/sports/${sportKey}/odds`;
  const params = new URLSearchParams({
    apiKey: API_KEY,
    regions: "us",
    markets: "h2h,spreads,totals",
    oddsFormat: "american",
  });

  console.log(`Fetching ${sport.toUpperCase()} games directly from The Odds API...`);
  console.log(`URL: ${url}?${params.toString().replace(API_KEY, "***")}\n`);

  try {
    const response = await fetch(`${url}?${params.toString()}`);
    
    if (!response.ok) {
      console.error(`API Error: ${response.status} ${response.statusText}`);
      const text = await response.text();
      console.error(text);
      process.exit(1);
    }

    const games = await response.json();
    console.log(`Total games returned by API: ${games.length}\n`);

    // Group by date
    const dateMap = new Map();
    games.forEach((g) => {
      const dt = new Date(g.commence_time);
      const dateStr = dt.toISOString().slice(0, 10);
      if (!dateMap.has(dateStr)) {
        dateMap.set(dateStr, []);
      }
      dateMap.get(dateStr).push(g);
    });

    console.log("Games by date (from The Odds API):");
    Array.from(dateMap.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .forEach(([date, gamesOnDate]) => {
        console.log(`  ${date}: ${gamesOnDate.length} games`);
        if (date === "2025-12-08") {
          console.log(`    Dec 8th games:`);
          gamesOnDate.forEach((g, idx) => {
            console.log(
              `      ${idx + 1}. ${g.away_team} @ ${g.home_team} @ ${g.commence_time}`
            );
          });
        }
      });

    // Check for Dec 8th specifically
    const dec8Games = games.filter((g) => {
      const dt = new Date(g.commence_time);
      return dt.toISOString().slice(0, 10) === "2025-12-08";
    });

    console.log(`\nGames on 2025-12-08: ${dec8Games.length}`);
    if (dec8Games.length === 0) {
      console.log(
        "\n⚠️  WARNING: The Odds API is not returning any games for Dec 8th, 2025."
      );
      console.log(
        "This could mean:\n" +
        "  1. Games aren't scheduled in The Odds API yet\n" +
        "  2. The API hasn't updated with those games\n" +
        "  3. There's a timezone issue\n"
      );
    }
  } catch (error) {
    console.error("Error:", error.message);
    process.exit(1);
  }
}

main();




