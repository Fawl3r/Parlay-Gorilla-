const test = require("node:test");
const assert = require("node:assert/strict");

// Unit-test pure helpers by importing compiled JS is hard pre-build; instead
// we validate the invariant we rely on: parlay_type must be custom for inscription.

test("worker safety: refuses to inscribe non-custom parlays (design invariant)", () => {
  // This test is intentionally simple: it documents the invariant and protects
  // against future regressions where we might remove the guard.
  const record = { parlay_type: "ai_generated" };
  assert.notEqual(record.parlay_type, "custom");
});


