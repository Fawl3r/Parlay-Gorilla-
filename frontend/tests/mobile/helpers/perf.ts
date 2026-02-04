import type { Page, TestInfo } from "@playwright/test";
import { expect } from "@playwright/test";

export type PerfBudget = {
  routeName: string;
  maxDomContentLoadedMs: number;
  maxNetworkIdleMs: number;
};

/**
 * Navigate to url, measure domcontentloaded + networkidle wait, attach perf JSON, enforce budgets.
 * Call setupAgeGateBypass(page) before this if testing prod with age gate.
 */
export async function measureRoutePerf(
  page: Page,
  testInfo: TestInfo,
  url: string,
  budget: PerfBudget,
): Promise<void> {
  const t0 = Date.now();
  const resp = await page.goto(url, { waitUntil: "domcontentloaded" });
  const domMs = Date.now() - t0;

  const t1 = Date.now();
  await page.waitForLoadState("networkidle", { timeout: 30_000 }).catch(() => {});
  const netIdleMs = Date.now() - t1;

  const payload = {
    route: budget.routeName,
    status: resp?.status() ?? null,
    domContentLoadedMs: domMs,
    networkIdleWaitMs: netIdleMs,
    url,
  };

  await testInfo.attach(`perf-${budget.routeName}.json`, {
    body: Buffer.from(JSON.stringify(payload, null, 2), "utf-8"),
    contentType: "application/json",
  });

  expect(
    domMs,
    `${budget.routeName} domcontentloaded over budget (${domMs}ms > ${budget.maxDomContentLoadedMs}ms)`,
  ).toBeLessThanOrEqual(budget.maxDomContentLoadedMs);

  expect(
    netIdleMs,
    `${budget.routeName} networkidle wait over budget (${netIdleMs}ms > ${budget.maxNetworkIdleMs}ms)`,
  ).toBeLessThanOrEqual(budget.maxNetworkIdleMs);
}
