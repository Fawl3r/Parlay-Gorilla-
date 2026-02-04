import type { Page, TestInfo } from "@playwright/test";

type MobileDiag = {
  consoleErrors: string[];
  requestFailures: string[];
  pageErrors: string[];
};

/**
 * Attach console errors, request failures, and page errors as mobile-diagnostics.txt
 * on test end. Call once per test (e.g. in beforeEach) with that test's page and testInfo.
 */
export function attachMobileDiagnostics(page: Page, testInfo: TestInfo): MobileDiag {
  const diag: MobileDiag = {
    consoleErrors: [],
    requestFailures: [],
    pageErrors: [],
  };

  page.on("console", (msg) => {
    if (msg.type() === "error" || msg.type() === "warning") {
      diag.consoleErrors.push(`[${msg.type()}] ${msg.text()}`);
    }
  });

  page.on("pageerror", (err) => {
    diag.pageErrors.push(err?.stack || err?.message || String(err));
  });

  page.on("requestfailed", (req) => {
    const failure = req.failure();
    diag.requestFailures.push(
      `${req.method()} ${req.url()} :: ${failure?.errorText || "unknown failure"}`,
    );
  });

  if (typeof (testInfo as { onTestFinished?: (fn: () => Promise<void>) => void }).onTestFinished === "function") {
    (testInfo as { onTestFinished: (fn: () => Promise<void>) => void }).onTestFinished(async () => {
      const lines = [
        "=== Mobile Diagnostics ===",
        "",
        `Console Errors/Warnings: ${diag.consoleErrors.length}`,
        ...diag.consoleErrors.map((x) => `- ${x}`),
        "",
        `Page Errors: ${diag.pageErrors.length}`,
        ...diag.pageErrors.map((x) => `- ${x}`),
        "",
        `Request Failures: ${diag.requestFailures.length}`,
        ...diag.requestFailures.map((x) => `- ${x}`),
        "",
      ].join("\n");

      await testInfo.attach("mobile-diagnostics.txt", {
        body: Buffer.from(lines, "utf-8"),
        contentType: "text/plain",
      });
    });
  }

  return diag;
}
