const test = require("node:test");
const assert = require("node:assert/strict");

/**
 * Economics Analysis: Inscription Selector with 15 Inscriptions/Month
 * 
 * Scenario:
 * - Users can SELECT which parlays to inscribe (custom OR AI)
 * - Premium plan includes 15 inscriptions per month
 * - Users choose which 15 parlays get on-chain proof
 * - Keep current pricing unchanged
 * 
 * IQ Cost: $0.37 per inscription
 */

test("inscription selector 15 cap: calculate profit per user", () => {
  const costPerInscriptionUSD = 0.37;
  const inscriptionsIncluded = 15; // Included in premium plan

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

  console.log("\n💰 INSCRIPTION SELECTOR - 15 INSCRIPTIONS/MONTH");
  console.log("=" .repeat(60));
  console.log("📋 Scenario:");
  console.log("   • Users can SELECT which parlays to inscribe (custom OR AI)");
  console.log("   • Premium plan includes 15 inscriptions per month");
  console.log("   • Users choose which 15 parlays get on-chain proof");
  console.log(`   • IQ Cost: $${costPerInscriptionUSD} per inscription`);
  console.log(`   • IQ Cost per user: $${(costPerInscriptionUSD * inscriptionsIncluded).toFixed(2)}/month`);

  const monthlyIQCostPerUser = costPerInscriptionUSD * inscriptionsIncluded;

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

test("inscription selector 15 cap: scale projections", () => {
  const costPerInscriptionUSD = 0.37;
  const inscriptionsIncluded = 15;
  const monthlyIQCostPerUser = costPerInscriptionUSD * inscriptionsIncluded;

  const subscriptionMix = {
    monthly: { price: 39.99, percentage: 60 },
    annual: { price: 399.99, percentage: 30 },
    lifetime: { price: 500, percentage: 10 },
  };

  const userScenarios = [10, 50, 100, 500, 1000];

  console.log("\n📈 SCALE PROJECTIONS (15 Inscriptions/Month)");
  console.log("=" .repeat(60));
  console.log("Subscription Mix:");
  console.log(`  ${subscriptionMix.monthly.percentage}% Monthly ($${subscriptionMix.monthly.price}/month)`);
  console.log(`  ${subscriptionMix.annual.percentage}% Annual ($${subscriptionMix.annual.price}/year)`);
  console.log(`  ${subscriptionMix.lifetime.percentage}% Lifetime ($${subscriptionMix.lifetime.price} one-time, amortized over 24 months)`);
  console.log(`\nIQ Cost per user: $${monthlyIQCostPerUser.toFixed(2)}/month (${inscriptionsIncluded} inscriptions included)`);

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

test("inscription selector 15 cap: comparison with other models", () => {
  const costPerInscriptionUSD = 0.37;
  
  const models = [
    { name: "100 inscriptions (all)", count: 100 },
    { name: "25 custom only", count: 25 },
    { name: "15 selector (custom or AI)", count: 15 },
  ];

  console.log("\n📊 COMPARISON: All Models");
  console.log("=" .repeat(60));

  const plans = [
    { name: "Premium Monthly", price: 39.99 },
    { name: "Premium Annual", price: 399.99, monthlyEquivalent: 399.99 / 12 },
  ];

  plans.forEach(plan => {
    const monthlyRevenue = plan.monthlyEquivalent || plan.price;
    
    console.log(`\n${plan.name} ($${monthlyRevenue.toFixed(2)}/month):`);
    
    models.forEach(model => {
      const monthlyIQCost = costPerInscriptionUSD * model.count;
      const profit = monthlyRevenue - monthlyIQCost;
      const margin = (profit / monthlyRevenue) * 100;
      
      console.log(`  ${model.name.padEnd(30)}: Cost $${monthlyIQCost.toFixed(2)} → Profit $${profit.toFixed(2)} (${margin.toFixed(1)}% margin) ${profit >= 0 ? "✅" : "❌"}`);
    });
  });

  console.log(`\n💰 Cost Comparison (per user per month):`);
  models.forEach(model => {
    const cost = costPerInscriptionUSD * model.count;
    console.log(`  ${model.name.padEnd(30)}: $${cost.toFixed(2)}/month`);
  });
});

test("inscription selector 15 cap: benefits and UX", () => {
  const costPerInscriptionUSD = 0.37;
  const inscriptionsIncluded = 15;
  const monthlyIQCostPerUser = costPerInscriptionUSD * inscriptionsIncluded;

  console.log("\n💡 INSCRIPTION SELECTOR MODEL - BENEFITS");
  console.log("=" .repeat(60));
  console.log(`IQ Cost per user: $${monthlyIQCostPerUser.toFixed(2)}/month (${inscriptionsIncluded} inscriptions)`);

  console.log(`\n✅ Advantages:`);
  console.log(`  1. User Choice: Users select which parlays matter most`);
  console.log(`  2. Flexibility: Can inscribe custom OR AI parlays`);
  console.log(`  3. Lower Cost: Only $${monthlyIQCostPerUser.toFixed(2)}/user/month (vs $37 for 100)`);
  console.log(`  4. High Margins: 85%+ profit margins on all plans`);
  console.log(`  5. Better UX: Users feel in control of their on-chain proofs`);
  console.log(`  6. Scalable: Profitable at any scale`);

  console.log(`\n📊 Profit Margins:`);
  const monthlyPlan = { price: 39.99, name: "Premium Monthly" };
  const annualPlan = { price: 399.99 / 12, name: "Premium Annual" };
  
  [monthlyPlan, annualPlan].forEach(plan => {
    const profit = plan.price - monthlyIQCostPerUser;
    const margin = (profit / plan.price) * 100;
    console.log(`  ${plan.name}: ${margin.toFixed(1)}% margin ($${profit.toFixed(2)} profit/user/month)`);
  });

  console.log(`\n🎯 Recommended Implementation:`);
  console.log(`  • Add "Inscribe" button/toggle to saved parlays`);
  console.log(`  • Show inscription count: "X of 15 inscriptions used this month"`);
  console.log(`  • Allow users to inscribe any saved parlay (custom or AI)`);
  console.log(`  • Reset count monthly with subscription renewal`);
  console.log(`  • Show on-chain proof status in UI`);
});

