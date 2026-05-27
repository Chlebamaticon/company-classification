import { test, expect } from "@playwright/test";

test.describe("Happy path", () => {
  test("submits form and displays FSC results", async ({ page }) => {
    await page.goto("/");

    await page.fill("#company_name", "Acme Manufacturing");
    await page.fill("#website_url", "https://acme-mfg.com");
    await page.click('button[type="submit"]');

    await expect(page.getByText("Progress")).toBeVisible();
    await expect(page.getByText("Document Ingestion")).toBeVisible();
    await expect(page.getByText("Website Crawl")).toBeVisible();
    await expect(page.getByText("FSC Classification")).toBeVisible();

    await expect(page.getByText("Classified FSC Codes")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("3408")).toBeVisible();
    await expect(page.getByText("3411")).toBeVisible();
    await expect(page.getByText("5945")).toBeVisible();
  });

  test("expands and collapses rationale", async ({ page }) => {
    await page.goto("/");
    await page.fill("#company_name", "Acme");
    await page.fill("#website_url", "https://acme.com");
    await page.click('button[type="submit"]');

    await expect(page.getByText("Classified FSC Codes")).toBeVisible({ timeout: 10_000 });

    const showBtn = page.getByText("Show rationale").first();
    await showBtn.click();
    await expect(page.getByText("Company manufactures CNC machining centers")).toBeVisible();

    await page.getByText("Hide rationale").first().click();
    await expect(page.getByText("Company manufactures CNC machining centers")).not.toBeVisible();
  });

  test("resets to form via Start New Classification", async ({ page }) => {
    await page.goto("/");
    await page.fill("#company_name", "Acme");
    await page.fill("#website_url", "https://acme.com");
    await page.click('button[type="submit"]');

    await expect(page.getByText("Classified FSC Codes")).toBeVisible({ timeout: 10_000 });

    await page.click("text=Start New Classification");

    await expect(page.locator("#company_name")).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toHaveText("Classify FSC Codes");
  });

  test("submits with optional email domain and file", async ({ page }) => {
    await page.goto("/");
    await page.fill("#company_name", "Acme Corp");
    await page.fill("#website_url", "https://acme.com");
    await page.fill("#email_domain", "acme.com");

    await expect(page.getByText("Classify FSC Codes")).toBeVisible();
    await page.click('button[type="submit"]');

    await expect(page.getByText("Classified FSC Codes")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("3408")).toBeVisible();
  });
});
