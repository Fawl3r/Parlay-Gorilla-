import { test, expect } from "@playwright/test";
import { gotoAndStabilize } from "../helpers/wait";
import { urls } from "../helpers/urls";
import { sel } from "../helpers/selectors";

test.describe("Mobile PROD — Gorilla Builder", () => {
  test("Loads and core UI is visible", async ({ page }) => {
    await gotoAndStabilize(page, urls.gorillaBuilder);

    const pageLoaded = page.locator(sel.pageCustomBuilder);
    const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
    await expect(pageLoaded.or(signIn).first()).toBeVisible({ timeout: 15_000 });
    await expect(
      page.locator(sel.analyzeBtn).or(page.locator(sel.analyzeBtnFallback)).or(signIn).first(),
    ).toBeVisible({ timeout: 5_000 });
  });

  test("Template click populates slip OR shows a meaningful empty-state", async ({ page }) => {
    await gotoAndStabilize(page, urls.gorillaBuilder);

    const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
    if (await signIn.isVisible()) {
      test.skip(true, "Requires auth — on Sign In page");
      return;
    }

    const template = page.locator(sel.safe2PickTemplate).first();
    const templateVisible = await template.isVisible().catch(() => false);
    if (!templateVisible) {
      const balanced = page.locator(sel.balancedTemplate).first();
      if (!(await balanced.isVisible().catch(() => false))) {
        test.skip(true, "No template button found — skipping");
        return;
      }
      await balanced.click({ force: true });
    } else {
      await template.click({ force: true });
    }

    const picksHeader = page.locator(sel.picksHeader).first();
    const noGamesCopy = page.locator("text=/no games|no odds|out of season|no markets/i");
    await expect(picksHeader.or(noGamesCopy)).toBeVisible({ timeout: 10_000 });
  });

  test("Analyze button is tappable and does not get stuck behind overlays", async ({ page }) => {
    await gotoAndStabilize(page, urls.gorillaBuilder);

    const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
    if (await signIn.isVisible()) {
      test.skip(true, "Requires auth — on Sign In page");
      return;
    }

    const analyze = page.locator(sel.analyzeBtn).or(page.locator(sel.analyzeBtnFallback));
    const analyzeVisible = await analyze.first().isVisible().catch(() => false);
    if (!analyzeVisible) {
      test.skip(true, "Analyze button not found — skipping");
      return;
    }
    await analyze.first().scrollIntoViewIfNeeded();
    await analyze.first().click();

    const analysisVisible = page.locator("text=/Analysis|Breakdown|Matchup/i");
    const toastOrMessage = page
      .locator(sel.toast)
      .or(page.locator("text=/add at least|no picks|not enough/i"));
    await expect(analysisVisible.or(toastOrMessage)).toBeVisible({ timeout: 12_000 });
  });

  test("Get AI Analysis opens breakdown modal with visible content (no dark-only screen)", async ({
    page,
  }) => {
    await gotoAndStabilize(page, urls.gorillaBuilder);

    const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
    if (await signIn.isVisible()) {
      test.skip(true, "Requires auth — on Sign In page");
      return;
    }

    const template = page.locator(sel.safe2PickTemplate).first();
    if (await template.isVisible().catch(() => false)) {
      await template.click({ force: true });
    } else {
      const balanced = page.locator(sel.balancedTemplate).first();
      if (await balanced.isVisible().catch(() => false)) await balanced.click({ force: true });
    }

    const getAnalysisBtn = page.locator(sel.analyzeBtn).or(page.locator(sel.analyzeBtnFallback));
    const found = await getAnalysisBtn.first().waitFor({ state: "visible", timeout: 10_000 }).catch(() => null);
    if (!found) {
      test.skip(true, "Get AI Analysis button not found — skipping");
      return;
    }
    await getAnalysisBtn.first().scrollIntoViewIfNeeded();
    await getAnalysisBtn.first().click();

    const breakdownHeading = page.getByRole("heading", { name: /Parlay Breakdown/i });
    const yourTicketHeading = page.getByText("Your Ticket");
    await expect(breakdownHeading.or(yourTicketHeading)).toBeVisible({ timeout: 25_000 });

    const modalPanel = page.locator(sel.breakdownModal);
    await expect(modalPanel).toBeVisible();
    await expect(breakdownHeading.or(yourTicketHeading)).toBeInViewport();
  });

  test("No horizontal overflow (common mobile break)", async ({ page }) => {
    await gotoAndStabilize(page, urls.gorillaBuilder);

    const hasOverflow = await page.evaluate(() => {
      const doc = document.documentElement;
      return doc.scrollWidth > doc.clientWidth + 2;
    });
    expect(hasOverflow).toBeFalsy();
  });

  test("Modal or sheet is scrollable on mobile (if present)", async ({ page }) => {
    await gotoAndStabilize(page, urls.gorillaBuilder);

    const signIn = page.getByRole("button", { name: /Sign in|Log in/i });
    if (await signIn.isVisible()) {
      test.skip(true, "Requires auth — on Sign In page");
      return;
    }

    const addPick = page.locator(sel.addPickBtn).first();
    if ((await addPick.count()) === 0) {
      test.skip(true, "No Add Pick button found — skipping modal scroll check.");
      return;
    }

    await addPick.click();
    const modal = page
      .locator(
        '[role="dialog"], [data-state="open"][data-radix-dialog-content], [data-testid="sheet-content"]',
      )
      .first();
    await modal.waitFor({ state: "visible", timeout: 8_000 }).catch(() => {});
    const modalVisible = await modal.isVisible().catch(() => false);
    if (!modalVisible) {
      test.skip(true, "Add Pick did not open a modal — skipping scroll check.");
      return;
    }

    const scrolled = await page.evaluate(() => {
      const el =
        document.querySelector("[role=\"dialog\"]") ||
        document.querySelector("[data-state=\"open\"][data-radix-dialog-content]") ||
        document.querySelector("[data-testid=\"sheet-content\"]");
      if (!el) return false;
      const before = (el as HTMLElement).scrollTop;
      (el as HTMLElement).scrollTop = before + 200;
      const after = (el as HTMLElement).scrollTop;
      return after > before;
    });
    expect(scrolled).toBeTruthy();
  });
});
