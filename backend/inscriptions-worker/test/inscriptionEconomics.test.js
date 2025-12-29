const test = require("node:test");
const assert = require("node:assert/strict");

/**
 * IQ Inscription Economics Calculator
 * 
 * This test calculates the costs and revenue for IQ inscriptions.
 * Based on observed transaction costs of ~0.37 SOL per inscription.
 */

test("inscription economics: calculate costs for 100 inscriptions per month", () => {
  const costPerInscriptionUSD = 0.37; // USD per inscription (observed)
  const inscriptionsPerMonth = 100;
  const totalCostPerMonthUSD = costPerInscriptionUSD * inscriptionsPerMonth;

  console.log("\n💰 IQ INSCRIPTION ECONOMICS");
  console.log("=" .repeat(60));
  console.log(`Cost per inscription: $${costPerInscriptionUSD} USD`);
  console.log(`Inscriptions per month: ${inscriptionsPerMonth}`);
  console.log(`Total cost per month: $${totalCostPerMonthUSD.toFixed(2)} USD`);
  console.log("\n📊 In SOL (at different SOL prices):");

  const solPrices = [50, 100, 150, 200, 250, 300]; // USD per SOL
  solPrices.forEach(price => {
    const costPerInscriptionSOL = costPerInscriptionUSD / price;
    const monthlyCostSOL = totalCostPerMonthUSD / price;
    const annualCostSOL = (totalCostPerMonthUSD * 12) / price;
    console.log(`\n  SOL @ $${price}:`);
    console.log(`    Per inscription: ${costPerInscriptionSOL.toFixed(6)} SOL`);
    console.log(`    Monthly: ${monthlyCostSOL.toFixed(4)} SOL ($${totalCostPerMonthUSD.toFixed(2)})`);
    console.log(`    Annual:  ${annualCostSOL.toFixed(4)} SOL ($${(totalCostPerMonthUSD * 12).toFixed(2)})`);
  });

  assert.ok(totalCostPerMonthUSD > 0, "Total cost should be positive");
});

test("inscription economics: calculate revenue for IQ at scale", () => {
  const costPerInscriptionUSD = 0.37; // USD per inscription
  const solPriceUSD = 150; // Example SOL price in USD
  const costPerInscriptionSOL = costPerInscriptionUSD / solPriceUSD;

  const scenarios = [
    { users: 10, inscriptionsPerUser: 100 },
    { users: 50, inscriptionsPerUser: 100 },
    { users: 100, inscriptionsPerUser: 100 },
    { users: 500, inscriptionsPerUser: 100 },
    { users: 1000, inscriptionsPerUser: 100 },
    { users: 100, inscriptionsPerUser: 10 }, // Light users
    { users: 100, inscriptionsPerUser: 50 }, // Medium users
    { users: 100, inscriptionsPerUser: 200 }, // Heavy users
  ];

  console.log("\n📈 REVENUE PROJECTIONS FOR IQ");
  console.log("=" .repeat(60));
  console.log(`Cost per inscription: $${costPerInscriptionUSD} USD`);
  console.log(`SOL price: $${solPriceUSD}`);
  console.log(`Cost per inscription: ${costPerInscriptionSOL.toFixed(6)} SOL`);
  console.log("\nMonthly Revenue Scenarios:");

  scenarios.forEach(({ users, inscriptionsPerUser }) => {
    const totalInscriptions = users * inscriptionsPerUser;
    const monthlyRevenueUSD = totalInscriptions * costPerInscriptionUSD;
    const monthlyRevenueSOL = monthlyRevenueUSD / solPriceUSD;
    const annualRevenueUSD = monthlyRevenueUSD * 12;
    const annualRevenueSOL = annualRevenueUSD / solPriceUSD;

    console.log(`\n  ${users} users × ${inscriptionsPerUser} inscriptions/user:`);
    console.log(`    Total inscriptions/month: ${totalInscriptions.toLocaleString()}`);
    console.log(`    Monthly revenue: ${monthlyRevenueSOL.toFixed(4)} SOL ($${monthlyRevenueUSD.toLocaleString(undefined, { maximumFractionDigits: 2 })})`);
    console.log(`    Annual revenue: ${annualRevenueSOL.toFixed(4)} SOL ($${annualRevenueUSD.toLocaleString(undefined, { maximumFractionDigits: 2 })})`);
  });
});

test("inscription economics: break down cost components", () => {
  const totalCostPerInscriptionUSD = 0.37; // USD per inscription
  const solPriceUSD = 150; // Example SOL price
  const totalCostPerInscriptionSOL = totalCostPerInscriptionUSD / solPriceUSD;

  // Estimated breakdown (these are approximations)
  // Actual breakdown depends on IQ's fee structure
  const estimatedBreakdownUSD = {
    solanaNetworkFee: 0.00075, // Very small network fee
    iqProtocolFee: 0.35, // Most of the cost (IQ's revenue) - ~94.6%
    dataStorageFee: 0.015, // On-chain data storage - ~4%
    other: 0.00425, // Miscellaneous - ~1.1%
  };

  console.log("\n🔍 COST BREAKDOWN (Estimated)");
  console.log("=" .repeat(60));
  console.log(`Total cost per inscription: $${totalCostPerInscriptionUSD} USD (${totalCostPerInscriptionSOL.toFixed(6)} SOL @ $${solPriceUSD}/SOL)`);
  console.log("\nEstimated breakdown:");

  Object.entries(estimatedBreakdownUSD).forEach(([component, costUSD]) => {
    const costSOL = costUSD / solPriceUSD;
    const percentage = (costUSD / totalCostPerInscriptionUSD) * 100;
    console.log(`  ${component.padEnd(20)}: $${costUSD.toFixed(4)} USD (${costSOL.toFixed(6)} SOL) - ${percentage.toFixed(2)}%`);
  });

  const totalEstimatedUSD = Object.values(estimatedBreakdownUSD).reduce((a, b) => a + b, 0);
  console.log(`\n  Total estimated:      $${totalEstimatedUSD.toFixed(4)} USD`);
  console.log(`  Difference:           $${Math.abs(totalCostPerInscriptionUSD - totalEstimatedUSD).toFixed(4)} USD`);
});

test("inscription economics: calculate for single user (100 inscriptions/month)", () => {
  const costPerInscriptionUSD = 0.37; // USD per inscription
  const inscriptionsPerMonth = 100;
  const solPriceUSD = 150; // Example price
  const costPerInscriptionSOL = costPerInscriptionUSD / solPriceUSD;

  const monthlyCostUSD = costPerInscriptionUSD * inscriptionsPerMonth;
  const monthlyCostSOL = monthlyCostUSD / solPriceUSD;
  const annualCostUSD = monthlyCostUSD * 12;
  const annualCostSOL = annualCostUSD / solPriceUSD;

  console.log("\n👤 SINGLE USER COST (100 inscriptions/month)");
  console.log("=" .repeat(60));
  console.log(`Cost per inscription: $${costPerInscriptionUSD} USD (${costPerInscriptionSOL.toFixed(6)} SOL @ $${solPriceUSD}/SOL)`);
  console.log(`Inscriptions per month: ${inscriptionsPerMonth}`);
  console.log(`\nMonthly cost:`);
  console.log(`  $${monthlyCostUSD.toFixed(2)} USD`);
  console.log(`  ${monthlyCostSOL.toFixed(4)} SOL`);
  console.log(`\nAnnual cost:`);
  console.log(`  $${annualCostUSD.toFixed(2)} USD`);
  console.log(`  ${annualCostSOL.toFixed(4)} SOL`);

  // Calculate what IQ makes from this user
  const estimatedIQFeePerInscriptionUSD = 0.35; // USD (most of the cost, ~94.6%)
  const iqRevenuePerMonthUSD = estimatedIQFeePerInscriptionUSD * inscriptionsPerMonth;
  const iqRevenuePerYearUSD = iqRevenuePerMonthUSD * 12;
  const iqRevenuePerMonthSOL = iqRevenuePerMonthUSD / solPriceUSD;
  const iqRevenuePerYearSOL = iqRevenuePerYearUSD / solPriceUSD;

  console.log(`\n💰 Estimated IQ revenue from this user:`);
  console.log(`  Monthly: $${iqRevenuePerMonthUSD.toFixed(2)} USD (${iqRevenuePerMonthSOL.toFixed(4)} SOL)`);
  console.log(`  Annual:  $${iqRevenuePerYearUSD.toFixed(2)} USD (${iqRevenuePerYearSOL.toFixed(4)} SOL)`);

  assert.ok(monthlyCostUSD > 0, "Monthly cost should be positive");
});

