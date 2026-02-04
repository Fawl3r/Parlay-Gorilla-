import type { Page } from "@playwright/test";

export type ApiTiming = { name: string; ms: number };
export type Mark = { name: string; ms: number };

export type UXProbeResults = {
  longTasksCount: number;
  worstLongTaskMs: number;
  apiTimings: ApiTiming[];
  marks: Mark[];
  tapToFeedbackMs?: number;
  timeToResultsMs?: number;
};

const LONG_TASK_SCRIPT = () => {
  (window as unknown as { __pgLongTasks?: number[] }).__pgLongTasks = [];
  try {
    const observer = new PerformanceObserver((list) => {
      const arr = (window as unknown as { __pgLongTasks: number[] }).__pgLongTasks;
      if (!arr) return;
      for (const entry of list.getEntries()) {
        if (entry.duration > 50) arr.push(entry.duration);
      }
    });
    observer.observe({ entryTypes: ["longtask"] });
  } catch {
    // longtask not supported
  }
};

const GET_LONG_TASKS_SCRIPT = (): { longTasksCount: number; worstLongTaskMs: number } => {
  const arr = (window as unknown as { __pgLongTasks?: number[] }).__pgLongTasks;
  if (!arr || !arr.length)
    return { longTasksCount: 0, worstLongTaskMs: 0 };
  return {
    longTasksCount: arr.length,
    worstLongTaskMs: Math.max(...arr),
  };
};

const networkTimings: ApiTiming[] = [];

/**
 * Installs the UX probe: long-task observer. Call once after page load, before the critical flow.
 */
export async function startUXProbe(page: Page): Promise<void> {
  await page.addInitScript(LONG_TASK_SCRIPT);
}

/**
 * Returns probe results (long tasks + any recorded API timings from installNetworkTimingListeners).
 * Call after the critical flow.
 */
export async function getUXProbeResults(page: Page): Promise<UXProbeResults> {
  const lt = await page.evaluate(GET_LONG_TASKS_SCRIPT);
  return {
    ...lt,
    apiTimings: [...networkTimings],
    marks: [],
  };
}

/**
 * Records request/response timings for URL patterns. Call before navigation or tap; timings are included in getUXProbeResults().
 */
export function installNetworkTimingListeners(page: Page, urlPatterns: (string | RegExp)[]): void {
  networkTimings.length = 0;
  const match = (url: string) =>
    urlPatterns.some((p) => (typeof p === "string" ? url.includes(p) : p.test(url)));

  page.on("request", (request) => {
    const u = request.url();
    if (!match(u)) return;
    (request as unknown as { __start?: number }).__start = Date.now();
  });

  page.on("response", (response) => {
    const request = response.request();
    const u = request.url();
    if (!match(u)) return;
    const start = (request as unknown as { __start?: number }).__start;
    if (typeof start === "number") {
      const ms = Date.now() - start;
      let name: string;
      try {
        name = new URL(u).pathname || u;
      } catch {
        name = u;
      }
      networkTimings.push({ name, ms });
    }
  });
}

export function getNetworkTimings(): ApiTiming[] {
  return [...networkTimings];
}

export function clearNetworkTimings(): void {
  networkTimings.length = 0;
}
