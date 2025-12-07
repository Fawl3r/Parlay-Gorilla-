/**
 * Win Probability Test Script
 * Verifies win probability calculation works for all sports
 * Run with: node test-win-probability.mjs
 */

// Mock the calculateModelProb function logic (mirrors the actual implementation)
function calculateModelProb(game, isHome) {
  const h2hMarket = game.markets.find(m => m.market_type === "h2h")
  if (!h2hMarket || h2hMarket.odds.length === 0) return 0.5
  
  const targetTeam = isHome ? game.home_team : game.away_team
  const targetTeamLower = targetTeam.toLowerCase()
  
  // Try to find matching odds
  let targetOdds = h2hMarket.odds.find(o => {
    const outcomeLower = o.outcome.toLowerCase()
    return outcomeLower === targetTeamLower || 
           outcomeLower.includes(targetTeamLower) || 
           targetTeamLower.includes(outcomeLower)
  })
  
  // If not found by team name, try positional
  if (!targetOdds && h2hMarket.odds.length >= 2) {
    targetOdds = isHome ? h2hMarket.odds[1] : h2hMarket.odds[0]
  }
  
  if (!targetOdds) return 0.5
  
  // Get implied probability
  let impliedProb
  if (typeof targetOdds.implied_prob === 'number') {
    impliedProb = targetOdds.implied_prob
  } else if (typeof targetOdds.implied_prob === 'string') {
    impliedProb = parseFloat(targetOdds.implied_prob)
  } else {
    const price = targetOdds.price
    if (price.startsWith('-')) {
      const odds = Math.abs(parseFloat(price))
      impliedProb = odds / (odds + 100)
    } else if (price.startsWith('+')) {
      const odds = parseFloat(price.substring(1))
      impliedProb = 100 / (odds + 100)
    } else {
      impliedProb = 0.5
    }
  }
  
  if (isNaN(impliedProb) || impliedProb <= 0 || impliedProb >= 1) {
    return 0.5
  }
  
  // Apply model adjustment
  const modelAdjustment = (impliedProb - 0.5) * 0.08
  const adjustedProb = impliedProb + modelAdjustment
  
  return Math.max(0.08, Math.min(0.92, adjustedProb))
}

console.log('🧪 Testing Win Probability Calculation\n')
console.log('='.repeat(60))

// Test cases for different sports and scenarios
const testCases = [
  {
    name: 'NFL - Favorite vs Underdog (numeric implied_prob)',
    game: {
      home_team: 'Kansas City Chiefs',
      away_team: 'Denver Broncos',
      markets: [{
        market_type: 'h2h',
        odds: [
          { outcome: 'Denver Broncos', price: '+275', implied_prob: 0.267 },
          { outcome: 'Kansas City Chiefs', price: '-345', implied_prob: 0.775 }
        ]
      }]
    },
    expectedHomeRange: [0.7, 0.85],
    expectedAwayRange: [0.2, 0.35]
  },
  {
    name: 'NBA - Close matchup (string implied_prob)',
    game: {
      home_team: 'Boston Celtics',
      away_team: 'Milwaukee Bucks',
      markets: [{
        market_type: 'h2h',
        odds: [
          { outcome: 'Milwaukee Bucks', price: '+110', implied_prob: '0.476' },
          { outcome: 'Boston Celtics', price: '-130', implied_prob: '0.565' }
        ]
      }]
    },
    expectedHomeRange: [0.5, 0.65],
    expectedAwayRange: [0.4, 0.55]
  },
  {
    name: 'NHL - Calculate from American odds (no implied_prob)',
    game: {
      home_team: 'Toronto Maple Leafs',
      away_team: 'Montreal Canadiens',
      markets: [{
        market_type: 'h2h',
        odds: [
          { outcome: 'Montreal Canadiens', price: '+180' },
          { outcome: 'Toronto Maple Leafs', price: '-220' }
        ]
      }]
    },
    expectedHomeRange: [0.6, 0.75],
    expectedAwayRange: [0.3, 0.45]
  },
  {
    name: 'MLB - Heavy favorite',
    game: {
      home_team: 'New York Yankees',
      away_team: 'Baltimore Orioles',
      markets: [{
        market_type: 'h2h',
        odds: [
          { outcome: 'Baltimore Orioles', price: '+400', implied_prob: 0.2 },
          { outcome: 'New York Yankees', price: '-500', implied_prob: 0.833 }
        ]
      }]
    },
    expectedHomeRange: [0.75, 0.92],
    expectedAwayRange: [0.08, 0.25]
  },
  {
    name: 'Soccer - Draw possible (2 team odds)',
    game: {
      home_team: 'Manchester City',
      away_team: 'Liverpool',
      markets: [{
        market_type: 'h2h',
        odds: [
          { outcome: 'Liverpool', price: '+200', implied_prob: 0.333 },
          { outcome: 'Manchester City', price: '-150', implied_prob: 0.6 }
        ]
      }]
    },
    expectedHomeRange: [0.55, 0.7],
    expectedAwayRange: [0.3, 0.45]
  },
  {
    name: 'Edge case - Empty markets',
    game: {
      home_team: 'Team A',
      away_team: 'Team B',
      markets: []
    },
    expectedHomeRange: [0.5, 0.5],
    expectedAwayRange: [0.5, 0.5]
  },
  {
    name: 'Edge case - No h2h market',
    game: {
      home_team: 'Team A',
      away_team: 'Team B',
      markets: [{
        market_type: 'spreads',
        odds: [{ outcome: 'Team A -3.5', price: '-110' }]
      }]
    },
    expectedHomeRange: [0.5, 0.5],
    expectedAwayRange: [0.5, 0.5]
  },
  {
    name: 'Partial team name match',
    game: {
      home_team: 'Green Bay Packers',
      away_team: 'Chicago Bears',
      markets: [{
        market_type: 'h2h',
        odds: [
          { outcome: 'Bears', price: '+150', implied_prob: 0.4 },
          { outcome: 'Packers', price: '-170', implied_prob: 0.63 }
        ]
      }]
    },
    expectedHomeRange: [0.55, 0.7],
    expectedAwayRange: [0.35, 0.5]
  }
]

let passed = 0
let failed = 0

for (const test of testCases) {
  const homeProb = calculateModelProb(test.game, true)
  const awayProb = calculateModelProb(test.game, false)
  
  const homeInRange = homeProb >= test.expectedHomeRange[0] && homeProb <= test.expectedHomeRange[1]
  const awayInRange = awayProb >= test.expectedAwayRange[0] && awayProb <= test.expectedAwayRange[1]
  const notNaN = !isNaN(homeProb) && !isNaN(awayProb)
  
  const success = homeInRange && awayInRange && notNaN
  
  if (success) {
    console.log(`\n✅ ${test.name}`)
    console.log(`   Home: ${(homeProb * 100).toFixed(1)}% (expected ${test.expectedHomeRange[0] * 100}-${test.expectedHomeRange[1] * 100}%)`)
    console.log(`   Away: ${(awayProb * 100).toFixed(1)}% (expected ${test.expectedAwayRange[0] * 100}-${test.expectedAwayRange[1] * 100}%)`)
    passed++
  } else {
    console.log(`\n❌ ${test.name}`)
    if (isNaN(homeProb) || isNaN(awayProb)) {
      console.log(`   ERROR: Got NaN! Home=${homeProb}, Away=${awayProb}`)
    } else {
      console.log(`   Home: ${(homeProb * 100).toFixed(1)}% ${homeInRange ? '✓' : '✗'} (expected ${test.expectedHomeRange[0] * 100}-${test.expectedHomeRange[1] * 100}%)`)
      console.log(`   Away: ${(awayProb * 100).toFixed(1)}% ${awayInRange ? '✓' : '✗'} (expected ${test.expectedAwayRange[0] * 100}-${test.expectedAwayRange[1] * 100}%)`)
    }
    failed++
  }
}

console.log('\n' + '='.repeat(60))
console.log(`\n📊 Results: ${passed} passed, ${failed} failed`)

// Verify probabilities sum check
console.log('\n📋 Additional Checks:')

const sampleGame = testCases[0].game
const hp = calculateModelProb(sampleGame, true)
const ap = calculateModelProb(sampleGame, false)
console.log(`   Probabilities sum to ~1.0: ${hp + ap} (${Math.abs(hp + ap - 1) < 0.15 ? '✓' : '✗'})`)
console.log(`   No NaN values: ${!isNaN(hp) && !isNaN(ap) ? '✓' : '✗'}`)
console.log(`   Values in valid range (0.08-0.92): ${hp >= 0.08 && hp <= 0.92 && ap >= 0.08 && ap <= 0.92 ? '✓' : '✗'}`)

if (failed === 0) {
  console.log('\n✅ All win probability tests passed!')
  process.exit(0)
} else {
  console.log('\n❌ Some tests failed!')
  process.exit(1)
}

