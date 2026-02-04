/**
 * UX and performance budgets for mobile gate tests.
 * Override via env: PG_BUDGET_*.
 * Cold = new context, no storage; warm = reuse. Gate can run cold only or both with different budgets.
 */
function envNum(key: string, fallback: number): number {
  const v = process.env[key];
  if (v === undefined || v === "") return fallback;
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

export const perfBudgets = {
  tapToFeedbackMs: envNum("PG_BUDGET_TAP_FEEDBACK_MS", 350),
  apiResponseMs: envNum("PG_BUDGET_API_MS", 2500),
  timeToResultsMs: envNum("PG_BUDGET_RESULTS_MS", 6000),
  worstLongTaskMs: envNum("PG_BUDGET_WORST_LONG_TASK_MS", 120),
  longTasksCount: envNum("PG_BUDGET_LONG_TASKS_COUNT", 3),
  // LCP-ish proxies (correlate with "feels fast")
  timeToFirstSkeletonMs: envNum("PG_BUDGET_TIME_TO_FIRST_SKELETON_MS", 500),
  spinnerVisibleDurationMs: envNum("PG_BUDGET_SPINNER_DURATION_MS", 4500),
  resultsVisibleMs: envNum("PG_BUDGET_RESULTS_VISIBLE_MS", 6000),
} as const;

/** Cold-load budgets (stricter when set). Use PG_BUDGET_COLD_* to override for first load. */
export const coldBudgets = {
  timeToResultsMs: envNum("PG_BUDGET_COLD_RESULTS_MS", 7000),
  tapToFeedbackMs: envNum("PG_BUDGET_COLD_TAP_FEEDBACK_MS", 450),
} as const;
