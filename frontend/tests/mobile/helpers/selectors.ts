/**
 * Stable selectors for mobile regression tests.
 * Prefer data-testid / data-page; fallbacks use text/role.
 * Use .first() or .or() in specs when multiple matches possible.
 */
export const sel = {
  header: "header",
  toast: '[role="status"], [data-sonner-toast], [data-testid="toast"]',

  // Page-loaded markers (route-specific; no guessing)
  pageCustomBuilder: '[data-page="custom-builder"]',
  pageAiBuilder: '[data-page="ai-builder"]',
  pageGames: '[data-page="games"]',

  // Gorilla Builder
  builderRoot: '[data-testid="custom-builder-page"]',
  builderRootFallback: "text=/Gorilla Parlay Builder|Custom Parlay Builder/i",
  builderGamesSection: "[data-custom-builder-games]",
  parlaySlip: '[data-testid="parlay-slip"]',
  picksHeader: "text=/Your picks|Your Picks|Your Parlay/i",
  analyzeBtn: '[data-testid="get-ai-analysis-btn"]',
  analyzeBtnFallback: 'button:has-text("Analyze")',
  saveBtn: 'button:has-text("Save")',
  clearBtn: 'button:has-text("Clear")',
  addPickBtn: 'button:has-text("Add pick")',

  safe2PickTemplate: "text=/Safer\\s+2[-\\s]?Pick/i",
  balancedTemplate: "text=/Balanced/i",
  degenTemplate: "text=/Degen/i",

  // Analysis modal
  breakdownModal: '[data-testid="parlay-breakdown-modal"]',

  // AI Picks
  aiPicksRoot: '[data-testid="ai-picks-page"]',
  aiPicksRootFallback: "text=/AI Picks|AI Parlay|Build.*parlay/i",
  generateBtn: 'button:has-text("Build")',
  legsInput: 'input[name="legs"]',
  sportPicker: 'button:has-text("Sport")',
  resultsCard: 'text=/Confidence/i',

  // PWA install
  pwaInstallCta: '[data-testid="pwa-install-cta"]',
} as const;
