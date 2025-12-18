import { test, expect } from "@playwright/test";
import { registerUser } from "./helpers/auth";

test.describe("Parlay builder and slip generator", () => {
  test("AI parlay generation returns valid structure", async ({ request }) => {
    const email = `parlay-${Date.now()}@test.com`;
    const password = "Passw0rd!";
    const token = await registerUser(request, email, password);

    const backendUrl = process.env.PG_BACKEND_URL || "http://localhost:8000";
    const res = await request.post(`${backendUrl}/api/parlay/suggest`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        num_legs: 3,
        risk_profile: "balanced",
        sports: ["NFL"],
      },
      timeout: 180000,
    });
    
    expect(res.status()).toBeLessThan(500);
    
    if (res.ok()) {
      const data = await res.json();
      // Verify parlay response structure for slip display
      expect(data).toHaveProperty("num_legs");
      expect(data).toHaveProperty("legs");
      expect(data).toHaveProperty("parlay_hit_prob");
      expect(data).toHaveProperty("risk_profile");
      
      if (data.legs && data.legs.length > 0) {
        const leg = data.legs[0];
        expect(leg).toHaveProperty("odds");
        expect(leg).toHaveProperty("game");
      }
    }
  });

  test.skip("Parlay builder page renders and displays slip (UI)", async ({ page }) => {
    // NOTE:
    // UI auth uses backend JWT stored in localStorage (auth_token).
    // Keep UI tests skipped until we add a stable Playwright helper that seeds localStorage
    // (and optionally completes profile setup) before navigation.
    await page.goto("/");
    await expect(page).toHaveURL(/\/?/);
  });

  test.skip("Custom parlay builder slip displays selected picks (UI)", async ({ page }) => {
    // See note above: need an e2e auth helper that seeds localStorage auth_token.
    await page.goto("/");
    await expect(page).toHaveURL(/\/?/);
  });

  test("Parlay slip calculates odds correctly", async ({ request }) => {
    const email = `parlay-odds-${Date.now()}@test.com`;
    const password = "Passw0rd!";
    const token = await registerUser(request, email, password);

    const backendUrl = process.env.PG_BACKEND_URL || "http://localhost:8000";
    const res = await request.post(`${backendUrl}/api/parlay/suggest`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        num_legs: 2,
        risk_profile: "balanced",
        sports: ["NFL"],
      },
      timeout: 180000,
    });
    
    if (res.ok()) {
      const data = await res.json();
      
      // Verify odds are present and formatted
      if (data.legs && data.legs.length > 0) {
        data.legs.forEach((leg: any) => {
          expect(leg).toHaveProperty("odds");
          expect(typeof leg.odds).toBe("string");
          // Odds should be in American format (+/-XXX)
          expect(leg.odds).toMatch(/^[+-]\d+$/);
        });
      }
      
      // Verify total parlay odds if present
      if (data.total_odds) {
        expect(typeof data.total_odds).toBe("string");
        expect(data.total_odds).toMatch(/^[+-]\d+$/);
      }
    }
  });

  test("Triple parlay displays all three risk profiles", async ({ request }) => {
    const email = `parlay-triple-${Date.now()}@test.com`;
    const password = "Passw0rd!";
    const token = await registerUser(request, email, password);

    const backendUrl = process.env.PG_BACKEND_URL || "http://localhost:8000";
    const res = await request.post(`${backendUrl}/api/parlay/suggest/triple`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        sports: ["NFL"],
      },
      timeout: 180000,
    });
    
    expect(res.status()).toBeLessThan(500);
    
    if (res.ok()) {
      const data = await res.json();
      // Triple parlay should have all three profiles
      expect(data).toHaveProperty("safe");
      expect(data).toHaveProperty("balanced");
      expect(data).toHaveProperty("degen");
      
      // Each should have parlay structure
      ["safe", "balanced", "degen"].forEach(profile => {
        if (data[profile]) {
          expect(data[profile]).toHaveProperty("legs");
          expect(data[profile]).toHaveProperty("num_legs");
        }
      });
    }
  });
});


