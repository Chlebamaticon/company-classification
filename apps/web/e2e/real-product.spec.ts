import { test, expect } from "@playwright/test";

/**
 * These tests run against the REAL docker-compose stack.
 * Prerequisites: `make up` (all services healthy).
 * Timeouts are longer to account for LLM + crawl latency.
 */

test.describe("Real product – happy path", () => {
  test("full classification flow with valid company", async ({ page }) => {
    await page.goto("/");

    await expect(page.locator("h1")).toHaveText("SalesPatriot");
    await expect(page.locator("#company_name")).toBeVisible();

    await page.fill("#company_name", "Lockheed Martin");
    await page.fill("#website_url", "https://www.lockheedmartin.com");
    await page.fill("#email_domain", "lockheedmartin.com");
    await page.click('button[type="submit"]');

    await expect(page.getByText("Progress")).toBeVisible({ timeout: 5_000 });

    // Wait for all stages to complete (real LLM + crawl can take up to ~90s)
    await expect(page.getByText("Classified FSC Codes")).toBeVisible({ timeout: 90_000 });

    // At least one FSC code card should render
    const codeCards = page.locator(".font-mono.text-2xl");
    await expect(codeCards.first()).toBeVisible();

    // Each code should be 4 digits
    const firstCode = await codeCards.first().textContent();
    expect(firstCode).toMatch(/^\d{4}$/);

    // Confidence bar should exist
    await expect(page.locator(".rounded-full.bg-green-500, .rounded-full.bg-yellow-500, .rounded-full.bg-red-400").first()).toBeVisible();
  });

  test("rationale toggle works on real results", async ({ page }) => {
    await page.goto("/");

    await page.fill("#company_name", "3M Company");
    await page.fill("#website_url", "https://www.3m.com");
    await page.click('button[type="submit"]');

    await expect(page.getByText("Classified FSC Codes")).toBeVisible({ timeout: 90_000 });

    const showBtn = page.getByText("Show rationale").first();
    await showBtn.click();

    // Rationale text should appear (non-empty paragraph)
    const rationale = page.locator("p.text-sm.leading-relaxed.text-gray-600").first();
    await expect(rationale).toBeVisible();
    const text = await rationale.textContent();
    expect(text!.length).toBeGreaterThan(10);

    await page.getByText("Hide rationale").first().click();
    await expect(rationale).not.toBeVisible();
  });

  test("start new classification resets to idle", async ({ page }) => {
    await page.goto("/");

    await page.fill("#company_name", "Boeing");
    await page.fill("#website_url", "https://www.boeing.com");
    await page.click('button[type="submit"]');

    await expect(page.getByText("Classified FSC Codes")).toBeVisible({ timeout: 90_000 });

    await page.click("text=Start New Classification");

    await expect(page.locator("#company_name")).toBeVisible();
    await expect(page.locator("#company_name")).toHaveValue("");
  });
});

test.describe("Real product – unhappy path", () => {
  test("form validation still works", async ({ page }) => {
    await page.goto("/");

    await page.click('button[type="submit"]');
    await expect(page.getByText("Company name is required.")).toBeVisible();
    await expect(page.getByText("Website URL is required.")).toBeVisible();
  });

  test("invalid URL is rejected before hitting API", async ({ page }) => {
    await page.goto("/");

    await page.fill("#company_name", "Test Corp");
    await page.fill("#website_url", "not-a-real-url");
    await page.click('button[type="submit"]');

    await expect(page.getByText("Enter a valid URL (http:// or https://).")).toBeVisible();
    // Should NOT have entered progress phase
    await expect(page.getByText("Progress")).not.toBeVisible();
  });

  test("unreachable website still returns classification (or graceful error)", async ({ page }) => {
    await page.goto("/");

    await page.fill("#company_name", "Nonexistent Corp");
    await page.fill("#website_url", "https://this-domain-does-not-exist-xyz123.com");
    await page.click('button[type="submit"]');

    await expect(page.getByText("Progress")).toBeVisible({ timeout: 5_000 });

    // Should either get results or a graceful error within timeout
    const outcome = page.getByText("Classified FSC Codes").or(page.locator(".text-red-700"));
    await expect(outcome).toBeVisible({ timeout: 90_000 });
  });
});
