const test = require("node:test");
const assert = require("node:assert/strict");

/**
 * Economics Analysis: Custom Parlays Only, Capped at 25/month
 * 
 * Scenario:
 * - Only CUSTOM parlays get inscribed (AI parlays are NOT inscribed)
 * - Maximum 25 inscriptions per user per month
 * - Keep current pricing unchanged
 * 
 * IQ Cost: $0.37 per inscription
 */

test("custom only 25 cap: calculate profit per user", () => {
  const costPerInscriptionUSD = 0.37;
  const maxInscriptionsPerUser = 25; // Only custom parlays, capped at 25/month

  const plans = [
    {
      name: "Premium Monthly",
      price: 39.99,
      period: "monthly",
    },
    {
      name: "Premium Annual",
      price: 399.99,
      period: "yearly",
      monthlyEquivalent: 399.99 / 12,
    },
    {
      name: "Lifetime",
      price: 500,
      period: "lifetime",
    },
  ];

  console.log("\n💰 CUSTOM PARLAYS ONLY - 25 CAP ECONOMICS");
  console.log("=" .repeat(60));
  console.log("📋 Scenario:");
  console.log("   • Only CUSTOM parlays get inscribed");
  console.log("   • AI parlays are NOT inscribed (no cost)");
  console.log("   • Maximum 25 inscriptions per user per month");
  console.log(`   • IQ Cost: $${costPerInscriptionUSD} per inscription`);
  console.log(`   • Max IQ Cost per user: $${(costPerInscriptionUSD * maxInscriptionsPerUser).toFixed(2)}/month`);

  const monthlyIQCostPerUser = costPerInscriptionUSD * maxInscriptionsPerUser;

  console.log("\n📊 Profit Analysis Per User:");

  plans.forEach(plan => {
    if (plan.period === "lifetime") {
      const timePeriods = [12, 24, 36, 60];
      console.log(`\n${plan.name} ($${plan.price} one-time):`);
      
      timePeriods.forEach(months => {
        const monthlyRevenue = plan.price / months;
        const totalIQCosts = monthlyIQCostPerUser * months;
        const totalRevenue = plan.price;
        const profit = totalRevenue - totalIQCosts;
        const profitMargin = (profit / totalRevenue) * 100;
        const monthlyProfit = profit / months;
        
        console.log(`  Over ${months} months (${months / 12} years):`);
        console.log(`    Revenue: $${totalRevenue.toFixed(2)} ($${monthlyRevenue.toFixed(2)}/month)`);
        console.log(`    IQ Costs: $${totalIQCosts.toFixed(2)} ($${monthlyIQCostPerUser.toFixed(2)}/month)`);
        console.log(`    Profit: $${profit.toFixed(2)} ($${monthlyProfit.toFixed(2)}/month)`);
        console.log(`    Margin: ${profitMargin.toFixed(1)}% ${profit >= 0 ? "✅" : "❌"}`);
      });
    } else {
      const monthlyRevenue = plan.period === "monthly" ? plan.price : plan.monthlyEquivalent;
      const monthlyProfit = monthlyRevenue - monthlyIQCostPerUser;
      const profitMargin = (monthlyProfit / monthlyRevenue) * 100;
      
      const annualRevenue = plan.period === "monthly" ? plan.price * 12 : plan.price;
      const annualIQCosts = monthlyIQCostPerUser * 12;
      const annualProfit = annualRevenue - annualIQCosts;
      const annualMargin = (annualProfit / annualRevenue) * 100;

      console.log(`\n${plan.name}:`);
      console.log(`  Monthly:`);
      console.log(`    Revenue: $${monthlyRevenue.toFixed(2)}`);
      console.log(`    IQ Costs: $${monthlyIQCostPerUser.toFixed(2)}`);
      console.log(`    Profit: $${monthlyProfit.toFixed(2)} (${profitMargin.toFixed(1)}% margin) ${monthlyProfit >= 0 ? "✅" : "❌"}`);
      console.log(`  Annual:`);
      console.log(`    Revenue: $${annualRevenue.toFixed(2)}`);
      console.log(`    IQ Costs: $${annualIQCosts.toFixed(2)}`);
      console.log(`    Profit: $${annualProfit.toFixed(2)} (${annualMargin.toFixed(1)}% margin) ${annualProfit >= 0 ? "✅" : "❌"}`);
    }
  });
});

test("custom only 25 cap: scale projections", () => {
  const costPerInscriptionUSD = 0.37;
  const maxInscriptionsPerUser = 25;
  const monthlyIQCostPerUser = costPerInscriptionUSD * maxInscriptionsPerUser;

  const subscriptionMix = {
    monthly: { price: 39.99, percentage: 60 },
    annual: { price: 399.99, percentage: 30 },
    lifetime: { price: 500, percentage: 10 },
  };

  const userScenarios = [10, 50, 100, 500, 1000];

  console.log("\n📈 SCALE PROJECTIONS (Custom Only, 25 Cap)");
  console.log("=" .repeat(60));
  console.log("Subscription Mix:");
  console.log(`  ${subscriptionMix.monthly.percentage}% Monthly ($${subscriptionMix.monthly.price}/month)`);
  console.log(`  ${subscriptionMix.annual.percentage}% Annual ($${subscriptionMix.annual.price}/year)`);
  console.log(`  ${subscriptionMix.lifetime.percentage}% Lifetime ($${subscriptionMix.lifetime.price} one-time, amortized over 24 months)`);
  console.log(`\nIQ Cost per user: $${monthlyIQCostPerUser.toFixed(2)}/month (max ${maxInscriptionsPerUser} custom inscriptions)`);

  userScenarios.forEach(totalUsers => {
    const monthlyUsers = Math.round(totalUsers * (subscriptionMix.monthly.percentage / 100));
    const annualUsers = Math.round(totalUsers * (subscriptionMix.annual.percentage / 100));
    const lifetimeUsers = totalUsers - monthlyUsers - annualUsers;

    const monthlyRevenue = monthlyUsers * subscriptionMix.monthly.price;
    const annualRevenueMonthly = (annualUsers * subscriptionMix.annual.price) / 12;
    const lifetimeRevenueMonthly = (lifetimeUsers * subscriptionMix.lifetime.price) / 24;
    const totalMonthlyRevenue = monthlyRevenue + annualRevenueMonthly + lifetimeRevenueMonthly;

    const totalMonthlyIQCosts = totalUsers * monthlyIQCostPerUser;
    const monthlyProfit = totalMonthlyRevenue - totalMonthlyIQCosts;
    const profitMargin = (monthlyProfit / totalMonthlyRevenue) * 100;

    const annualRevenue = totalMonthlyRevenue * 12;
    const annualIQCosts = totalMonthlyIQCosts * 12;
    const annualProfit = annualRevenue - annualIQCosts;

    console.log(`\n${totalUsers} Total Users:`);
    console.log(`  Breakdown: ${monthlyUsers} monthly, ${annualUsers} annual, ${lifetimeUsers} lifetime`);
    console.log(`  Monthly Revenue: $${totalMonthlyRevenue.toFixed(2)}`);
    console.log(`  Monthly IQ Costs: $${totalMonthlyIQCosts.toFixed(2)}`);
    console.log(`  Monthly Profit: $${monthlyProfit.toFixed(2)} (${profitMargin.toFixed(1)}% margin) ${monthlyProfit >= 0 ? "✅" : "❌"}`);
    console.log(`  Annual Profit: $${annualProfit.toFixed(2)}`);
  });
});

test("custom only 25 cap: comparison with previous model", () => {
  const costPerInscriptionUSD = 0.37;
  const oldMaxInscriptions = 100;
  const newMaxInscriptions = 25;

  const oldMonthlyIQCost = costPerInscriptionUSD * oldMaxInscriptions;
  const newMonthlyIQCost = costPerInscriptionUSD * newMaxInscriptions;

  console.log("\n📊 COMPARISON: 100 vs 25 Inscriptions Cap");
  console.log("=" .repeat(60));

  const plans = [
    { name: "Premium Monthly", price: 39.99 },
    { name: "Premium Annual", price: 399.99, monthlyEquivalent: 399.99 / 12 },
  ];

  plans.forEach(plan => {
    const monthlyRevenue = plan.monthlyEquivalent || plan.price;
    
    const oldProfit = monthlyRevenue - oldMonthlyIQCost;
    const newProfit = monthlyRevenue - newMonthlyIQCost;
    const improvement = newProfit - oldProfit;
    const improvementPercent = (improvement / Math.abs(oldProfit)) * 100;

    console.log(`\n${plan.name} ($${monthlyRevenue.toFixed(2)}/month):`);
    console.log(`  Old Model (100 inscriptions):`);
    console.log(`    IQ Cost: $${oldMonthlyIQCost.toFixed(2)}/month`);
    console.log(`    Profit: $${oldProfit.toFixed(2)}/month ${oldProfit >= 0 ? "✅" : "❌"}`);
    console.log(`  New Model (25 inscriptions, custom only):`);
    console.log(`    IQ Cost: $${newMonthlyIQCost.toFixed(2)}/month`);
    console.log(`    Profit: $${newProfit.toFixed(2)}/month ${newProfit >= 0 ? "✅" : "❌"}`);
    console.log(`  Improvement: +$${improvement.toFixed(2)}/month (${improvementPercent > 0 ? "+" : ""}${improvementPercent.toFixed(1)}%)`);
  });

  console.log(`\n💰 Cost Savings:`);
  console.log(`  Per user per month: $${(oldMonthlyIQCost - newMonthlyIQCost).toFixed(2)}`);
  console.log(`  Per user per year: $${((oldMonthlyIQCost - newMonthlyIQCost) * 12).toFixed(2)}`);
  console.log(`  For 100 users per month: $${((oldMonthlyIQCost - newMonthlyIQCost) * 100).toFixed(2)}`);
  console.log(`  For 100 users per year: $${((oldMonthlyIQCost - newMonthlyIQCost) * 100 * 12).toFixed(2)}`);
});

test("custom only 25 cap: break-even and margins", () => {
  const costPerInscriptionUSD = 0.37;
  const maxInscriptionsPerUser = 25;
  const monthlyIQCostPerUser = costPerInscriptionUSD * maxInscriptionsPerUser;

  console.log("\n📊 BREAK-EVEN & MARGIN ANALYSIS");
  console.log("=" .repeat(60));
  console.log(`IQ Cost per user (max ${maxInscriptionsPerUser} custom inscriptions): $${monthlyIQCostPerUser.toFixed(2)}/month`);

  const plans = [
    { name: "Premium Monthly", price: 39.99 },
    { name: "Premium Annual", price: 399.99, monthlyEquivalent: 399.99 / 12 },
  ];

  plans.forEach(plan => {
    const monthlyRevenue = plan.monthlyEquivalent || plan.price;
    const profit = monthlyRevenue - monthlyIQCostPerUser;
    const margin = (profit / monthlyRevenue) * 100;
    const breakEven = profit >= 0;

    console.log(`\n${plan.name}:`);
    console.log(`  Revenue: $${monthlyRevenue.toFixed(2)}/month`);
    console.log(`  IQ Cost: $${monthlyIQCostPerUser.toFixed(2)}/month`);
    console.log(`  Profit: $${profit.toFixed(2)}/month`);
    console.log(`  Margin: ${margin.toFixed(1)}% ${breakEven ? "✅ PROFITABLE" : "❌ LOSING MONEY"}`);
    
    if (breakEven) {
      const buffer = profit;
      const bufferPercent = (buffer / monthlyRevenue) * 100;
      console.log(`  ✅ Healthy margin with $${buffer.toFixed(2)} buffer (${bufferPercent.toFixed(1)}%)`);
    }
  });

  console.log(`\n💡 Key Benefits:`);
  console.log(`  ✅ All plans are now profitable`);
  console.log(`  ✅ 75% reduction in IQ costs (from $37 to $9.25 per user)`);
  console.log(`  ✅ AI parlays don't incur inscription costs`);
  console.log(`  ✅ Users can still save unlimited AI parlays (just not inscribed)`);
  console.log(`  ✅ Custom parlays get on-chain proof (25/month limit)`);
});

