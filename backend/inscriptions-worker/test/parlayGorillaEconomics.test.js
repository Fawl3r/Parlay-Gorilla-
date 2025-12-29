const test = require("node:test");
const assert = require("node:assert/strict");

/**
 * Parlay Gorilla Economics Analysis
 * 
 * This analyzes the cost/revenue model for Parlay Gorilla inscriptions.
 * Currently, inscriptions are a COST, not revenue - unless monetized.
 */

test("parlay gorilla economics: current cost model", () => {
  const costPerInscriptionUSD = 0.37; // USD - what YOU pay to IQ
  const inscriptionsPerMonth = 100; // Per user
  const solPriceUSD = 150;

  console.log("\n💰 PARLAY GORILLA INSCRIPTION ECONOMICS");
  console.log("=" .repeat(60));
  console.log("⚠️  CURRENT SITUATION: Inscriptions are a COST, not revenue");
  console.log("\n📉 Cost per inscription: $0.37 USD (paid to IQ)");
  console.log("📉 This is money LEAVING your business, not coming in");
  
  const monthlyCostPerUser = costPerInscriptionUSD * inscriptionsPerMonth;
  const annualCostPerUser = monthlyCostPerUser * 12;

  console.log("\n💸 Cost per user (100 inscriptions/month):");
  console.log(`   Monthly: $${monthlyCostPerUser.toFixed(2)} USD`);
  console.log(`   Annual:  $${annualCostPerUser.toFixed(2)} USD`);

  // Scale costs
  const userScenarios = [10, 50, 100, 500, 1000];
  console.log("\n📊 Total Monthly Costs at Scale:");
  userScenarios.forEach(users => {
    const totalInscriptions = users * inscriptionsPerMonth;
    const totalCost = totalInscriptions * costPerInscriptionUSD;
    console.log(`   ${users} users: $${totalCost.toFixed(2)}/month (${totalInscriptions.toLocaleString()} inscriptions)`);
  });
});

test("parlay gorilla economics: monetization strategies", () => {
  const costPerInscriptionUSD = 0.37;
  const solPriceUSD = 150;

  console.log("\n💡 MONETIZATION STRATEGIES");
  console.log("=" .repeat(60));

  // Strategy 1: Charge users per inscription
  console.log("\n1️⃣  CHARGE PER INSCRIPTION:");
  const markupPercentages = [10, 25, 50, 100, 200];
  markupPercentages.forEach(markup => {
    const priceToUser = costPerInscriptionUSD * (1 + markup / 100);
    const profitPerInscription = priceToUser - costPerInscriptionUSD;
    const profitMargin = (profitPerInscription / priceToUser) * 100;
    console.log(`   ${markup}% markup: Charge $${priceToUser.toFixed(2)} → Profit $${profitPerInscription.toFixed(2)} (${profitMargin.toFixed(1)}% margin)`);
  });

  // Strategy 2: Subscription tiers
  console.log("\n2️⃣  SUBSCRIPTION TIERS:");
  const subscriptionTiers = [
    { name: "Free", inscriptions: 0, price: 0 },
    { name: "Basic", inscriptions: 10, price: 9.99 },
    { name: "Pro", inscriptions: 50, price: 19.99 },
    { name: "Premium", inscriptions: 100, price: 29.99 },
    { name: "Unlimited", inscriptions: 999, price: 49.99 },
  ];

  subscriptionTiers.forEach(tier => {
    if (tier.inscriptions === 0) {
      console.log(`   ${tier.name.padEnd(12)}: $${tier.price.toFixed(2)}/month - ${tier.inscriptions} inscriptions`);
    } else {
      const cost = tier.inscriptions * costPerInscriptionUSD;
      const profit = tier.price - cost;
      const profitMargin = tier.price > 0 ? (profit / tier.price) * 100 : 0;
      const breakEven = cost <= tier.price ? "✅" : "❌";
      console.log(`   ${tier.name.padEnd(12)}: $${tier.price.toFixed(2)}/month - ${tier.inscriptions} inscriptions`);
      console.log(`              Cost: $${cost.toFixed(2)} → Profit: $${profit.toFixed(2)} (${profitMargin.toFixed(1)}% margin) ${breakEven}`);
    }
  });

  // Strategy 3: Credit packs
  console.log("\n3️⃣  CREDIT PACKS:");
  const creditPacks = [
    { credits: 10, price: 4.99 },
    { credits: 25, price: 9.99 },
    { credits: 50, price: 17.99 },
    { credits: 100, price: 29.99 },
  ];

  creditPacks.forEach(pack => {
    const cost = pack.credits * costPerInscriptionUSD;
    const profit = pack.price - cost;
    const profitMargin = (profit / pack.price) * 100;
    const pricePerCredit = pack.price / pack.credits;
    console.log(`   ${pack.credits} credits: $${pack.price.toFixed(2)} ($${pricePerCredit.toFixed(2)}/credit)`);
    console.log(`              Cost: $${cost.toFixed(2)} → Profit: $${profit.toFixed(2)} (${profitMargin.toFixed(1)}% margin)`);
  });
});

test("parlay gorilla economics: break-even analysis", () => {
  const costPerInscriptionUSD = 0.37;
  const inscriptionsPerMonth = 100;

  console.log("\n📊 BREAK-EVEN ANALYSIS");
  console.log("=" .repeat(60));
  console.log("To break even, you need to charge at least what you pay:");
  console.log(`   Minimum price per inscription: $${costPerInscriptionUSD}`);
  console.log(`   Minimum monthly subscription (100 inscriptions): $${(costPerInscriptionUSD * inscriptionsPerMonth).toFixed(2)}`);

  console.log("\n💡 Recommended Pricing:");
  console.log("   Option A: Charge $0.50 per inscription");
  console.log("     → Profit: $0.13 per inscription (26% margin)");
  console.log("     → 100 inscriptions = $50 revenue, $37 cost, $13 profit");
  
  console.log("\n   Option B: $9.99/month for 25 inscriptions");
  console.log("     → Cost: $9.25, Profit: $0.74 (7.4% margin)");
  
  console.log("\n   Option C: $19.99/month for 50 inscriptions");
  console.log("     → Cost: $18.50, Profit: $1.49 (7.5% margin)");
  
  console.log("\n   Option D: $29.99/month for 100 inscriptions");
  console.log("     → Cost: $37.00, Loss: -$7.01 ❌ (need to increase price)");
  
  console.log("\n   Option E: $39.99/month for 100 inscriptions");
  console.log("     → Cost: $37.00, Profit: $2.99 (7.5% margin) ✅");
});

test("parlay gorilla economics: revenue projections with monetization", () => {
  const costPerInscriptionUSD = 0.37;
  const solPriceUSD = 150;

  // Assume you charge $0.50 per inscription (35% markup)
  const pricePerInscription = 0.50;
  const profitPerInscription = pricePerInscription - costPerInscriptionUSD;
  const profitMargin = (profitPerInscription / pricePerInscription) * 100;

  console.log("\n💰 REVENUE PROJECTIONS (Charging $0.50 per inscription)");
  console.log("=" .repeat(60));
  console.log(`Price per inscription: $${pricePerInscription}`);
  console.log(`Cost per inscription: $${costPerInscriptionUSD}`);
  console.log(`Profit per inscription: $${profitPerInscription} (${profitMargin.toFixed(1)}% margin)`);

  const scenarios = [
    { users: 10, inscriptionsPerUser: 100 },
    { users: 50, inscriptionsPerUser: 100 },
    { users: 100, inscriptionsPerUser: 100 },
    { users: 500, inscriptionsPerUser: 100 },
    { users: 1000, inscriptionsPerUser: 100 },
  ];

  console.log("\nMonthly Revenue Scenarios:");
  scenarios.forEach(({ users, inscriptionsPerUser }) => {
    const totalInscriptions = users * inscriptionsPerUser;
    const revenue = totalInscriptions * pricePerInscription;
    const costs = totalInscriptions * costPerInscriptionUSD;
    const profit = revenue - costs;
    const profitMarginTotal = (profit / revenue) * 100;

    console.log(`\n  ${users} users × ${inscriptionsPerUser} inscriptions/user:`);
    console.log(`    Revenue: $${revenue.toLocaleString(undefined, { maximumFractionDigits: 2 })}`);
    console.log(`    Costs:   $${costs.toLocaleString(undefined, { maximumFractionDigits: 2 })}`);
    console.log(`    Profit:  $${profit.toLocaleString(undefined, { maximumFractionDigits: 2 })} (${profitMarginTotal.toFixed(1)}% margin)`);
  });
});

