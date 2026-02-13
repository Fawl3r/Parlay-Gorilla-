import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { SafetySnapshotView } from "@/app/admin/safety/page";
import type { SafetySnapshotResponse } from "@/lib/api/types/system";

describe("SafetySnapshotView", () => {
  it("renders state, reasons, and events when provided", () => {
    const snap: SafetySnapshotResponse = {
      state: "YELLOW",
      reasons: ["odds_data_stale", "api_budget_ratio >= 0.8"],
      telemetry: { error_count_5m: 2 },
      safety_mode_enabled: true,
      events: [
        { ts: 1700000000, from_state: "GREEN", to_state: "YELLOW", reasons: ["odds_data_stale"] },
      ],
      health_score: 55,
      recommended_action: "Review reasons; check refresh jobs and API budget.",
    };
    const html = renderToStaticMarkup(<SafetySnapshotView snap={snap} />);
    expect(html).toContain("YELLOW");
    expect(html).toContain("odds_data_stale");
    expect(html).toContain("api_budget_ratio");
    expect(html).toContain("GREEN");
    expect(html).toContain("Timeline");
    expect(html).toContain("55");
    expect(html).toContain("Review reasons");
  });

  it("does not crash when telemetry keys are missing", () => {
    const minimalSnap: SafetySnapshotResponse = {
      state: "GREEN",
      reasons: [],
      telemetry: {},
      safety_mode_enabled: true,
    };
    expect(() =>
      renderToStaticMarkup(<SafetySnapshotView snap={minimalSnap} />)
    ).not.toThrow();
    const html = renderToStaticMarkup(<SafetySnapshotView snap={minimalSnap} />);
    expect(html).toContain("GREEN");
    expect(html).toContain("Key telemetry");
  });
});
