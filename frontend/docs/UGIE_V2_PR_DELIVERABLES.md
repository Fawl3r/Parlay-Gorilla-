# UGIE v2 Frontend Wiring — PR Deliverables

## Summary

Frontend wiring for UGIE v2: API types, normalizer passthrough, view model builder, and analysis detail UI modules. When `analysis_content.ugie_v2` is present, the analysis page renders UGIE modules (Top Factors, Availability Impact, Matchup Mismatches, Game Script, Market Edge, Confidence & Risk, Weather Impact, Data Quality Notice) and hides legacy matchup breakdown cards. When `ugie_v2` is absent, behavior is unchanged (legacy matchup cards render).

## Modified / New Files

### New
- `frontend/lib/analysis/detail/AnalysisDetailViewModel.ts` — View model types (extracted from builder).
- `frontend/lib/analysis/detail/ugie/UgieV2ModulesBuilder.ts` — Builds `UgieModulesViewModel` from `UgieV2`.
- `frontend/components/analysis/detail/UgieTopFactors.tsx`
- `frontend/components/analysis/detail/UgieAvailabilityImpact.tsx`
- `frontend/components/analysis/detail/UgieMatchupMismatches.tsx`
- `frontend/components/analysis/detail/UgieGameScript.tsx`
- `frontend/components/analysis/detail/UgieMarketEdge.tsx`
- `frontend/components/analysis/detail/UgieConfidenceRisk.tsx`
- `frontend/components/analysis/detail/UgieWeatherImpact.tsx`
- `frontend/components/analysis/detail/UgieDataQualityNotice.tsx`

### Modified
- `frontend/lib/api/types/analysis.ts` — Added `UgieSignal`, `UgiePillar`, `UgieDataQuality`, `UgieWeatherBlock`, `UgieV2`; extended `GameAnalysisContent` with `ugie_v2?: UgieV2`.
- `frontend/lib/analysis/AnalysisContentNormalizer.ts` — Passthrough `ugie_v2` and optional FREE-mode keys.
- `frontend/lib/analysis/detail/AnalysisDetailViewModelBuilder.ts` — Imports types from new file; when `ugie_v2` exists, builds `ugieModules` via `UgieV2ModulesBuilder`, sets `matchupCards: []`, attaches `ugieModules`.
- `frontend/components/analysis/detail/index.ts` — Exports new UGIE components.
- `frontend/app/analysis/[...slug]/AnalysisPageClient.tsx` — Imports UGIE components; when `viewModel.ugieModules` exists renders UGIE modules in order and does not render `MatchupBreakdownCard` list; otherwise renders legacy matchup cards.

## How to Run Frontend Checks

```bash
cd frontend
npm run lint
npm run build
# Optional: npm run test:unit
```

## Legacy Behavior When `ugie_v2` Missing

- `AnalysisDetailViewModelBuilder` does not set `ugieModules` when `analysis.analysis_content.ugie_v2` is missing.
- `AnalysisPageClient` renders `viewModel.matchupCards` (legacy `MatchupBreakdownCard` list) when `viewModel.ugieModules` is absent.
- No changes to API contract or existing analysis content keys; `ugie_v2` is optional.

## Manual QA Checklist

- **NFL (outdoor):** Weather module visible when rules fire or `weather_missing`; confidence/risk and data quality as expected.
- **MLB / Soccer (outdoor):** Same as NFL for weather.
- **NBA (indoor):** Weather module not shown (or only neutral “weather missing” if backend sends it for that sport).
- **UFC/Boxing (thin data):** Data quality notice and confidence cap/disclaimer when status ≠ Good.

## Screenshots for PR

1. **NFL (with weather):** Analysis detail with UGIE modules and Weather Impact visible.
2. **NBA (no weather):** Analysis detail with UGIE modules, no Weather Impact.
3. **Thin-data (e.g. UFC):** Analysis detail with Data Quality Notice and confidence disclaimer.

Capture after running the app and opening an analysis page that has `ugie_v2` in the response (and one without for legacy comparison if desired).
