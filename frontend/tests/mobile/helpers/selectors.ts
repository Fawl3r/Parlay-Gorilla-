/**
 * Stable selectors for mobile regression tests.
 * Prefer data-testid / data-page; fallbacks use text/role.
 * Use .first() or .or() in specs when multiple matches possible.
 */
export const sel = {
  header: "header",
  toast: '[role="status"], [data-sonner-toast], [data-testid="pg-toast"], [data-testid="toast"]',

  // Page-loaded markers (route-specific; no guessing)
  pageCustomBuilder: '[data-page="custom-builder"]',
  pageAiBuilder: '[data-page="ai-builder"]',
  pageGames: '[data-page="games"]',

  // Gorilla Builder (pg-builder-root after deploy; data-page works on current prod)
  builderRoot: '[data-testid="pg-builder-root"], [data-page="custom-builder"]',
  builderRootFallback: "text=/Gorilla Parlay Builder|Custom Parlay Builder/i",
  builderGamesSection: "[data-custom-builder-games]",
  parlaySlip: '[data-testid="parlay-slip"]',
  picksHeader: "text=/Your picks|Your Picks|Your Parlay/i",
  analyzeBtn: '[data-testid="pg-analyze-slip"], [data-testid="get-ai-analysis-btn"]',
  analyzeBtnFallback: 'button:has-text("Analyze"), button:has-text("Get AI Analysis")',
  saveBtn: '[data-testid="pg-save-slip"], button:has-text("Save")',
  clearBtn: 'button:has-text("Clear")',
  addPickBtn: '[data-testid="pg-add-pick"], button:has-text("Add pick")',

  safe2PickTemplate: "text=/Safer\\s+2[-\\s]?Pick/i",
  balancedTemplate: "text=/Balanced/i",
  degenTemplate: "text=/Degen/i",

  // Analysis modal
  breakdownModal: '[data-testid="parlay-breakdown-modal"]',

  // AI Picks
  aiPicksRoot: '[data-testid="pg-ai-picks-root"], [data-testid="ai-picks-page"]',
  aiPicksRootFallback: "text=/AI Picks|AI Parlay|Build.*parlay/i",
  generateBtn: '[data-testid="pg-ai-generate"], button:has-text("Build")',
  legsInput: 'input[name="legs"]',
  sportPicker: 'button:has-text("Sport")',
  resultsCard: '[data-testid="pg-ai-results"], text=/Confidence/i',
  paywall: '[data-testid="pg-paywall"]',
  skeleton: '[data-testid="pg-skeleton"]',

  // PWA install
  pwaInstallCta: '[data-testid="pwa-install-cta"]',
} as const;
