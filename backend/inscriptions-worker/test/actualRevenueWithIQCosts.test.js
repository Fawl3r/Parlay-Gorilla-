const test = require("node:test");
const assert = require("node:assert/strict");

/**
 * Actual Revenue Analysis with IQ Inscription Costs
 * 
 * Based on your current pricing:
 * - Premium Monthly: $39.99/month
 * - Premium Annual: $399.99/year  
 * - Lifetime: $500 one-time
 * 
 * Scenario: Each user gets 100 parlays (AI + custom combined) that can be inscribed
 * IQ Cost: $0.37 per inscription
 */

test("actual revenue: calculate profit per user with IQ costs", () => {
  const costPerInscriptionUSD = 0.37;
  const parlaysPerUser = 100; // Total parlays (AI + custom) that can be inscribed

  const plans = [
    {
      name: "Premium Monthly",
      price: 39.99,
      period: "monthly",
      description: "$39.99/month",
    },
    {
      name: "Premium Annual",
      price: 399.99,
      period: "yearly",
      description: "$399.99/year (equivalent to $33.33/month)",
      monthlyEquivalent: 399.99 / 12,
    },
    {
      name: "Lifetime",
      price: 500,
      period: "lifetime",
      description: "$500 one-time",
      // For lifetime, we'll calculate over different time periods
    },
  ];

  console.log("\n💰 ACTUAL REVENUE ANALYSIS WITH IQ COSTS");
  console.log("=" .repeat(60));
  console.log(`IQ Cost per inscription: $${costPerInscriptionUSD}`);
  console.log(`Parlays per user (inscribable): ${parlaysPerUser}`);
  console.log(`Total IQ cost per user (if all inscribed): $${(costPerInscriptionUSD * parlaysPerUser).toFixed(2)}`);
  console.log("\n📊 Profit Analysis Per User:");

  plans.forEach(plan => {
    if (plan.period === "lifetime") {
      // Calculate for different time periods
      const timePeriods = [12, 24, 36, 60]; // months
      console.log(`\n${plan.name} (${plan.description}):`);
      
      timePeriods.forEach(months => {
        const monthlyRevenue = plan.price / months;
        const totalIQCosts = costPerInscriptionUSD * parlaysPerUser * months;
        const totalRevenue = plan.price;
        const profit = totalRevenue - totalIQCosts;
        const profitMargin = (profit / totalRevenue) * 100;
        const monthlyProfit = profit / months;
        
        console.log(`  Over ${months} months (${months / 12} years):`);
        console.log(`    Revenue: $${totalRevenue.toFixed(2)} ($${monthlyRevenue.toFixed(2)}/month)`);
        console.log(`    IQ Costs: $${totalIQCosts.toFixed(2)} ($${(totalIQCosts / months).toFixed(2)}/month)`);
        console.log(`    Profit: $${profit.toFixed(2)} ($${monthlyProfit.toFixed(2)}/month)`);
        console.log(`    Margin: ${profitMargin.toFixed(1)}% ${profit >= 0 ? "✅" : "❌"}`);
      });
    } else {
      const monthlyRevenue = plan.period === "monthly" ? plan.price : plan.monthlyEquivalent;
      const monthlyIQCosts = costPerInscriptionUSD * parlaysPerUser;
      const monthlyProfit = monthlyRevenue - monthlyIQCosts;
      const profitMargin = (monthlyProfit / monthlyRevenue) * 100;
      
      const annualRevenue = plan.period === "monthly" ? plan.price * 12 : plan.price;
      const annualIQCosts = monthlyIQCosts * 12;
      const annualProfit = annualRevenue - annualIQCosts;
      const annualMargin = (annualProfit / annualRevenue) * 100;

      console.log(`\n${plan.name} (${plan.description}):`);
      console.log(`  Monthly:`);
      console.log(`    Revenue: $${monthlyRevenue.toFixed(2)}`);
      console.log(`    IQ Costs: $${monthlyIQCosts.toFixed(2)}`);
      console.log(`    Profit: $${monthlyProfit.toFixed(2)} (${profitMargin.toFixed(1)}% margin) ${monthlyProfit >= 0 ? "✅" : "❌"}`);
      console.log(`  Annual:`);
      console.log(`    Revenue: $${annualRevenue.toFixed(2)}`);
      console.log(`    IQ Costs: $${annualIQCosts.toFixed(2)}`);
      console.log(`    Profit: $${annualProfit.toFixed(2)} (${annualMargin.toFixed(1)}% margin) ${annualProfit >= 0 ? "✅" : "❌"}`);
    }
  });
});

test("actual revenue: scale projections with IQ costs", () => {
  const costPerInscriptionUSD = 0.37;
  const parlaysPerUser = 100;

  // Assume mix of subscription types
  const subscriptionMix = {
    monthly: { price: 39.99, percentage: 60 }, // 60% monthly subscribers
    annual: { price: 399.99, percentage: 30 }, // 30% annual subscribers
    lifetime: { price: 500, percentage: 10 }, // 10% lifetime (amortized over 24 months)
  };

  const userScenarios = [10, 50, 100, 500, 1000];

  console.log("\n📈 SCALE PROJECTIONS WITH IQ COSTS");
  console.log("=" .repeat(60));
  console.log("Subscription Mix:");
  console.log(`  ${subscriptionMix.monthly.percentage}% Monthly ($${subscriptionMix.monthly.price}/month)`);
  console.log(`  ${subscriptionMix.annual.percentage}% Annual ($${subscriptionMix.annual.price}/year)`);
  console.log(`  ${subscriptionMix.lifetime.percentage}% Lifetime ($${subscriptionMix.lifetime.price} one-time, amortized over 24 months)`);
  console.log(`\nIQ Cost per user: $${(costPerInscriptionUSD * parlaysPerUser).toFixed(2)}/month (if all ${parlaysPerUser} parlays inscribed)`);

  userScenarios.forEach(totalUsers => {
    const monthlyUsers = Math.round(totalUsers * (subscriptionMix.monthly.percentage / 100));
    const annualUsers = Math.round(totalUsers * (subscriptionMix.annual.percentage / 100));
    const lifetimeUsers = totalUsers - monthlyUsers - annualUsers;

    // Calculate monthly revenue
    const monthlyRevenue = monthlyUsers * subscriptionMix.monthly.price;
    const annualRevenueMonthly = (annualUsers * subscriptionMix.annual.price) / 12;
    const lifetimeRevenueMonthly = (lifetimeUsers * subscriptionMix.lifetime.price) / 24; // Amortized over 24 months
    const totalMonthlyRevenue = monthlyRevenue + annualRevenueMonthly + lifetimeRevenueMonthly;

    // Calculate monthly IQ costs
    const totalMonthlyIQCosts = totalUsers * costPerInscriptionUSD * parlaysPerUser;

    // Calculate profit
    const monthlyProfit = totalMonthlyRevenue - totalMonthlyIQCosts;
    const profitMargin = (monthlyProfit / totalMonthlyRevenue) * 100;

    // Annual projections
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

test("actual revenue: break-even analysis", () => {
  const costPerInscriptionUSD = 0.37;
  const parlaysPerUser = 100;
  const monthlyIQCostPerUser = costPerInscriptionUSD * parlaysPerUser;

  const plans = [
    { name: "Premium Monthly", price: 39.99 },
    { name: "Premium Annual", price: 399.99, monthlyEquivalent: 399.99 / 12 },
  ];

  console.log("\n📊 BREAK-EVEN ANALYSIS");
  console.log("=" .repeat(60));
  console.log(`IQ Cost per user (${parlaysPerUser} inscriptions): $${monthlyIQCostPerUser.toFixed(2)}/month`);

  plans.forEach(plan => {
    const monthlyRevenue = plan.monthlyEquivalent || plan.price;
    const profit = monthlyRevenue - monthlyIQCostPerUser;
    const breakEven = profit >= 0;
    
    console.log(`\n${plan.name}:`);
    console.log(`  Monthly Revenue: $${monthlyRevenue.toFixed(2)}`);
    console.log(`  Monthly IQ Cost: $${monthlyIQCostPerUser.toFixed(2)}`);
    console.log(`  Monthly Profit: $${profit.toFixed(2)} ${breakEven ? "✅ PROFITABLE" : "❌ LOSING MONEY"}`);
    
    if (!breakEven) {
      const neededPrice = monthlyIQCostPerUser;
      const currentShortfall = monthlyIQCostPerUser - monthlyRevenue;
      console.log(`  ⚠️  Need to increase price by $${currentShortfall.toFixed(2)} to break even`);
      console.log(`  ⚠️  Or reduce inscriptions to ${Math.floor(monthlyRevenue / costPerInscriptionUSD)} per user`);
    }
  });
});

test("actual revenue: optimal pricing recommendations", () => {
  const costPerInscriptionUSD = 0.37;
  const parlaysPerUser = 100;
  const monthlyIQCostPerUser = costPerInscriptionUSD * parlaysPerUser;

  console.log("\n💡 OPTIMAL PRICING RECOMMENDATIONS");
  console.log("=" .repeat(60));
  console.log(`Current IQ Cost: $${monthlyIQCostPerUser.toFixed(2)}/user/month (${parlaysPerUser} inscriptions)`);
  
  const currentMonthly = 39.99;
  const currentAnnual = 399.99;
  
  console.log(`\nCurrent Pricing:`);
  console.log(`  Monthly: $${currentMonthly}/month`);
  console.log(`  Annual: $${currentAnnual}/year ($${(currentAnnual / 12).toFixed(2)}/month)`);
  
  const monthlyProfit = currentMonthly - monthlyIQCostPerUser;
  const annualMonthlyProfit = (currentAnnual / 12) - monthlyIQCostPerUser;
  
  console.log(`\nCurrent Profitability:`);
  console.log(`  Monthly Plan: $${monthlyProfit.toFixed(2)}/user/month ${monthlyProfit >= 0 ? "✅" : "❌"}`);
  console.log(`  Annual Plan: $${annualMonthlyProfit.toFixed(2)}/user/month ${annualMonthlyProfit >= 0 ? "✅" : "❌"}`);
  
  // Recommendations
  console.log(`\n💡 Recommendations:`);
  
  if (monthlyProfit < 0) {
    const neededMonthly = monthlyIQCostPerUser * 1.1; // 10% margin
    console.log(`  Monthly: Increase to $${neededMonthly.toFixed(2)}/month (10% margin)`);
  } else {
    const margin = (monthlyProfit / currentMonthly) * 100;
    console.log(`  Monthly: Current price is profitable (${margin.toFixed(1)}% margin)`);
  }
  
  if (annualMonthlyProfit < 0) {
    const neededAnnual = monthlyIQCostPerUser * 12 * 1.1; // 10% margin
    console.log(`  Annual: Increase to $${neededAnnual.toFixed(2)}/year ($${(neededAnnual / 12).toFixed(2)}/month)`);
  } else {
    const margin = (annualMonthlyProfit / (currentAnnual / 12)) * 100;
    console.log(`  Annual: Current price is profitable (${margin.toFixed(1)}% margin)`);
  }
  
  // Alternative: Limit inscriptions
  const maxInscriptionsAtCurrentPrice = Math.floor(currentMonthly / costPerInscriptionUSD);
  console.log(`\n  Alternative: Limit to ${maxInscriptionsAtCurrentPrice} inscriptions/user at current $${currentMonthly}/month price`);
});

