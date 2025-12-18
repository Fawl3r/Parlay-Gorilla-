/**
 * Simple Routing Test Script
 * Run with: node test-routing.mjs
 */

// Mock the generateAnalysisUrl function logic (kept in sync with backend)
function calculateNflWeekUtc(gameDate) {
  const seasonStarts = {
    2024: { month: 9, day: 5 },
    2025: { month: 9, day: 4 },
    2026: { month: 9, day: 10 },
  }

  const toUtcDateOnly = (d) => new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()))
  const pyWeekday = (jsDay) => (jsDay + 6) % 7 // JS: 0=Sun..6=Sat -> Python: 0=Mon..6=Sun

  const seasonYear = gameDate.getUTCFullYear()
  const known = seasonStarts[seasonYear]

  let seasonStart
  if (known) {
    seasonStart = new Date(Date.UTC(seasonYear, known.month - 1, known.day))
  } else {
    const sept1 = new Date(Date.UTC(seasonYear, 8, 1))
    const daysUntilThursday = ((3 - pyWeekday(sept1.getUTCDay())) % 7 + 7) % 7
    seasonStart = new Date(Date.UTC(seasonYear, 8, 1 + daysUntilThursday))
  }

  const gameDateOnly = toUtcDateOnly(gameDate)
  if (gameDateOnly.getTime() < seasonStart.getTime()) return null

  const daysSinceStart = Math.floor((gameDateOnly.getTime() - seasonStart.getTime()) / (24 * 60 * 60 * 1000))
  const week = Math.floor(daysSinceStart / 7) + 1
  return week > 18 ? null : week
}

function generateAnalysisUrl(sport, awayTeam, homeTeam, startTime, week) {
  const cleanTeam = (name) =>
    String(name || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")

  const awayClean = cleanTeam(awayTeam)
  const homeClean = cleanTeam(homeTeam)
  const sportLower = String(sport || "").toLowerCase()

  const gameDate = new Date(startTime)
  const yearUtc = Number.isFinite(gameDate.getTime()) ? gameDate.getUTCFullYear() : new Date().getUTCFullYear()

  // NFL uses week format (canonical slug)
  if (sportLower === "nfl") {
    const weekToken = Number.isFinite(week) ? week : calculateNflWeekUtc(gameDate)
    const normalizedWeek = weekToken == null ? "None" : weekToken
    return `/analysis/nfl/${awayClean}-vs-${homeClean}-week-${normalizedWeek}-${yearUtc}`
  }

  const dateStr = gameDate.toISOString().slice(0, 10)
  return `/analysis/${sportLower}/${awayClean}-vs-${homeClean}-${dateStr}`
}

console.log('🧪 Testing Analysis URL Generation\n')
console.log('='.repeat(60))

const tests = [
  {
    name: 'NFL game with week',
    sport: 'nfl',
    awayTeam: 'Chicago Bears',
    homeTeam: 'Green Bay Packers',
    startTime: '2025-12-07T20:00:00Z',
    week: 14,
    expected: '/analysis/nfl/chicago-bears-vs-green-bay-packers-week-14-2025',
  },
  {
    name: 'NBA game with date',
    sport: 'nba',
    awayTeam: 'Los Angeles Lakers',
    homeTeam: 'Boston Celtics',
    startTime: '2025-01-15T20:00:00Z',
    week: null,
    expected: '/analysis/nba/los-angeles-lakers-vs-boston-celtics-2025-01-15',
  },
  {
    name: 'NHL game with special characters',
    sport: 'nhl',
    awayTeam: 'New York Rangers',
    homeTeam: 'Toronto Maple Leafs',
    startTime: '2025-01-15T20:00:00Z',
    week: null,
    expected: '/analysis/nhl/new-york-rangers-vs-toronto-maple-leafs-2025-01-15',
  },
  {
    name: 'NFL without week (should compute week)',
    sport: 'nfl',
    awayTeam: 'Dallas Cowboys',
    homeTeam: 'Philadelphia Eagles',
    startTime: '2025-09-15T20:00:00Z',
    week: null,
    expected: '/analysis/nfl/dallas-cowboys-vs-philadelphia-eagles-week-2-2025',
  },
]

let passed = 0
let failed = 0

for (const test of tests) {
  const result = generateAnalysisUrl(
    test.sport,
    test.awayTeam,
    test.homeTeam,
    test.startTime,
    test.week
  )
  
  if (result === test.expected) {
    console.log(`✅ ${test.name}`)
    console.log(`   Generated: ${result}`)
    passed++
  } else {
    console.log(`❌ ${test.name}`)
    console.log(`   Expected:  ${test.expected}`)
    console.log(`   Got:       ${result}`)
    failed++
  }
  console.log()
}

console.log('='.repeat(60))
console.log(`\n📊 Results: ${passed} passed, ${failed} failed\n`)

if (failed === 0) {
  console.log('✅ All routing tests passed!')
  process.exit(0)
} else {
  console.log('❌ Some routing tests failed!')
  process.exit(1)
}

