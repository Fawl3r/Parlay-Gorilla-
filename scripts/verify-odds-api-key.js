/**
 * Verify The Odds API key and check quota usage.
 * 
 * Uses response headers to show quota information:
 * - x-requests-remaining: Credits remaining
 * - x-requests-used: Credits used since last reset
 * - x-requests-last: Cost of last API call
 * 
 * Usage:
 *   node scripts/verify-odds-api-key.js
 */

const fs = require("fs");
const path = require("path");

// Load .env file
const envPath = path.join(__dirname, "..", "backend", ".env");
let apiKeyFromEnv = null;

if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, "utf8");
  envContent.split("\n").forEach((line) => {
    const match = line.match(/^([^#=]+)=(.*)$/);
    if (match) {
      const key = match[1].trim();
      const value = match[2].trim().replace(/^["']|["']$/g, "");
      if (key === "THE_ODDS_API_KEY" || key === "the_odds_api_key") {
        apiKeyFromEnv = value;
      }
    }
  });
}

// Dashboard key for comparison (replace with your actual key)
const DASHBOARD_KEY = "your_dashboard_key_here";

console.log("=".repeat(60));
console.log("The Odds API Key Verification");
console.log("=".repeat(60));
console.log();

// Compare keys
console.log("API Key Comparison:");
console.log(`  Dashboard Key: ${DASHBOARD_KEY}`);
console.log(`  .env Key:      ${apiKeyFromEnv || "NOT FOUND"}`);
if (apiKeyFromEnv) {
  if (apiKeyFromEnv === DASHBOARD_KEY) {
    console.log(`  ✅ Keys MATCH`);
  } else {
    console.log(`  ⚠️  Keys DO NOT MATCH - Using different key!`);
  }
} else {
  console.log(`  ❌ API key not found in .env file`);
  process.exit(1);
}
console.log();

// Test with /sports endpoint (doesn't count against quota)
async function testSportsEndpoint() {
  console.log("Testing /v4/sports endpoint (free, no quota cost)...");
  const url = `https://api.the-odds-api.com/v4/sports?apiKey=${apiKeyFromEnv}`;
  
  try {
    const response = await fetch(url);
    const headers = {
      remaining: response.headers.get("x-requests-remaining"),
      used: response.headers.get("x-requests-used"),
      last: response.headers.get("x-requests-last"),
    };
    
    if (!response.ok) {
      const text = await response.text();
      console.log(`  ❌ Error: ${response.status} ${response.statusText}`);
      console.log(`  Response: ${text}`);
      return null;
    }
    
    const sports = await response.json();
    console.log(`  ✅ Success! Found ${sports.length} sports`);
    console.log(`  Quota Headers:`);
    console.log(`    x-requests-remaining: ${headers.remaining || "N/A"}`);
    console.log(`    x-requests-used: ${headers.used || "N/A"}`);
    console.log(`    x-requests-last: ${headers.last || "N/A"}`);
    console.log();
    
    return headers;
  } catch (error) {
    console.log(`  ❌ Error: ${error.message}`);
    return null;
  }
}

// Test with a small odds request (will use quota)
async function testOddsEndpoint() {
  console.log("Testing /v4/sports/basketball_nba/odds endpoint...");
  const url = `https://api.the-odds-api.com/v4/sports/basketball_nba/odds`;
  const params = new URLSearchParams({
    apiKey: apiKeyFromEnv,
    regions: "us",
    markets: "h2h",
    oddsFormat: "american",
  });
  
  try {
    const response = await fetch(`${url}?${params.toString()}`);
    const headers = {
      remaining: response.headers.get("x-requests-remaining"),
      used: response.headers.get("x-requests-used"),
      last: response.headers.get("x-requests-last"),
    };
    
    if (!response.ok) {
      const text = await response.text();
      console.log(`  ❌ Error: ${response.status} ${response.statusText}`);
      console.log(`  Response: ${text.substring(0, 200)}`);
      return null;
    }
    
    const games = await response.json();
    console.log(`  ✅ Success! Found ${games.length} NBA games`);
    console.log(`  Quota Headers:`);
    console.log(`    x-requests-remaining: ${headers.remaining || "N/A"}`);
    console.log(`    x-requests-used: ${headers.used || "N/A"}`);
    console.log(`    x-requests-last: ${headers.last || "N/A"}`);
    console.log();
    
    // Show date distribution
    const dateMap = new Map();
    games.forEach((g) => {
      const dt = new Date(g.commence_time);
      const dateStr = dt.toISOString().slice(0, 10);
      if (!dateMap.has(dateStr)) {
        dateMap.set(dateStr, []);
      }
      dateMap.get(dateStr).push(g);
    });
    
    console.log("  Games by date:");
    Array.from(dateMap.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .slice(0, 10) // Show first 10 dates
      .forEach(([date, gamesOnDate]) => {
        console.log(`    ${date}: ${gamesOnDate.length} games`);
      });
    console.log();
    
    return headers;
  } catch (error) {
    console.log(`  ❌ Error: ${error.message}`);
    return null;
  }
}

async function main() {
  // Test 1: Sports endpoint (free)
  const sportsHeaders = await testSportsEndpoint();
  
  // Test 2: Odds endpoint (uses quota)
  const oddsHeaders = await testOddsEndpoint();
  
  // Summary
  console.log("=".repeat(60));
  console.log("Summary:");
  console.log("=".repeat(60));
  
  if (sportsHeaders && sportsHeaders.remaining !== null) {
    const remaining = parseInt(sportsHeaders.remaining);
    const used = parseInt(sportsHeaders.used);
    const total = remaining + used;
    const percentUsed = total > 0 ? ((used / total) * 100).toFixed(1) : "0.0";
    
    console.log(`Quota Status: ${used} / ${total} used (${percentUsed}%)`);
    console.log(`Remaining: ${remaining} requests`);
    console.log();
    
    if (remaining === 0) {
      console.log("⚠️  QUOTA EXHAUSTED - No requests remaining!");
      console.log("   Quota resets on the 1st of each month at 12AM UTC");
      console.log("   Next reset: " + getNextResetDate());
    } else if (remaining < 50) {
      console.log("⚠️  Low quota remaining - consider upgrading plan");
    } else {
      console.log("✅ Quota looks healthy");
    }
  } else {
    console.log("⚠️  Could not determine quota status from headers");
  }
}

function getNextResetDate() {
  const now = new Date();
  const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  nextMonth.setUTCHours(0, 0, 0, 0);
  return nextMonth.toISOString();
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});




