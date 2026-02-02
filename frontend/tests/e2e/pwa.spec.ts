import { test, expect } from "@playwright/test";

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified";

test.beforeEach(async ({ page }) => {
  await page.addInitScript((key: string) => {
    localStorage.setItem(key, "true");
  }, AGE_VERIFIED_KEY);
});

test.describe("PWA installability (manifest + icons + service worker)", () => {
  test("page includes manifest link and PWA meta tags", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    const manifestLink = page.locator('link[rel="manifest"]');
    await expect(manifestLink).toHaveAttribute("href", "/manifest.json");

    await expect(page.locator('meta[name="theme-color"]').first()).toHaveAttribute("content", "#00e676");
    await expect(page.locator('meta[name="apple-mobile-web-app-capable"]').first()).toHaveAttribute("content", "yes");
  });

  test("manifest and PWA icons return 200", async ({ request }) => {
    const manifestRes = await request.get("/manifest.json");
    expect(manifestRes.ok(), "manifest.json should be 200").toBe(true);

    const icon192Res = await request.get("/icons/icon-192.png");
    expect(icon192Res.ok(), "/icons/icon-192.png should be 200").toBe(true);

    const icon512Res = await request.get("/icons/icon-512.png");
    expect(icon512Res.ok(), "/icons/icon-512.png should be 200").toBe(true);
  });

  test("manifest JSON has required PWA fields", async ({ request }) => {
    const res = await request.get("/manifest.json");
    expect(res.ok()).toBe(true);
    const manifest = (await res.json()) as { name?: string; start_url?: string; icons?: unknown[] };
    expect(manifest.name).toBe("Parlay Gorilla");
    expect(manifest.start_url).toBe("/app");
    expect(Array.isArray(manifest.icons) && manifest.icons.length >= 2).toBe(true);
  });

  test("service worker registers after load", async ({ page }) => {
    await page.goto("/", { waitUntil: "load" });

    // Registration runs on window.load; poll for SW to appear (up to 10s).
    const deadline = Date.now() + 10_000;
    let hasRegistration = false;
    while (Date.now() < deadline) {
      hasRegistration = await page.evaluate(async () => {
        if (!("serviceWorker" in navigator)) return false;
        const reg = await navigator.serviceWorker.getRegistration();
        return reg != null;
      });
      if (hasRegistration) break;
      await new Promise((r) => setTimeout(r, 300));
    }

    expect(hasRegistration, "service worker should be registered after load").toBe(true);
  });
});
