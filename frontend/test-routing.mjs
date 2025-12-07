/**
 * Simple Routing Test Script
 * Run with: node test-routing.mjs
 */

// Mock the generateAnalysisUrl function logic
function generateAnalysisUrl(sport, awayTeam, homeTeam, startTime, week) {
  const cleanTeam = (name) => 
    name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  
  const awayClean = cleanTeam(awayTeam)
  const homeClean = cleanTeam(homeTeam)
  const sportLower = sport.toLowerCase()
  
  const gameDate = new Date(startTime)
  const year = gameDate.getFullYear()
  
  if (sportLower === 'nfl' && week) {
    return `/analysis/${sportLower}/${awayClean}-vs-${homeClean}-week-${week}-${year}`
  } else {
    const dateStr = gameDate.toISOString().split('T')[0]
    return `/analysis/${sportLower}/${awayClean}-vs-${homeClean}-${dateStr}`
  }
}

console.log('🧪 Testing Analysis URL Generation\n')
console.log('='.repeat(60))

const tests = [
  {
    name: 'NFL game with week',
    sport: 'nfl',
    awayTeam: 'Chicago Bears',
    homeTeam: 'Green Bay Packers',
    startTime: '2025-01-15T20:00:00Z',
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
    name: 'NFL without week (should use date)',
    sport: 'nfl',
    awayTeam: 'Dallas Cowboys',
    homeTeam: 'Philadelphia Eagles',
    startTime: '2025-01-15T20:00:00Z',
    week: null,
    expected: '/analysis/nfl/dallas-cowboys-vs-philadelphia-eagles-2025-01-15',
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

