/**
 * Removes explainer text from plan names like "(Card)", "(Crypto)", etc.
 * This keeps the UI clean while preserving backend data structure.
 */
export function formatPlanName(planName: string | null | undefined): string {
  if (!planName) return "Free Plan"
  
  // Remove common explainer patterns in parentheses
  return planName
    .replace(/\s*\(Card\)/gi, "")
    .replace(/\s*\(Crypto\)/gi, "")
    .replace(/\s*\(Monthly\)/gi, "")
    .replace(/\s*\(Annual\)/gi, "")
    .replace(/\s*\(Yearly\)/gi, "")
    .replace(/\s*\(explainer\)/gi, "")
    .replace(/\s*\(Explainer\)/gi, "")
    .trim()
}

