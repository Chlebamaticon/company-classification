import { test, expect } from "@playwright/test";

test.describe("Unhappy path – validation", () => {
  test("shows both errors when form submitted empty", async ({ page }) => {
    await page.goto("/");
    await page.click('button[type="submit"]');

    await expect(page.getByText("Company name is required.")).toBeVisible();
    await expect(page.getByText("Website URL is required.")).toBeVisible();
  });

  test("shows only company name error when URL is filled", async ({ page }) => {
    await page.goto("/");
    await page.fill("#website_url", "https://example.com");
    await page.click('button[type="submit"]');

    await expect(page.getByText("Company name is required.")).toBeVisible();
    await expect(page.getByText("Website URL is required.")).not.toBeVisible();
  });

  test("shows only URL error when company name is filled", async ({ page }) => {
    await page.goto("/");
    await page.fill("#company_name", "Acme");
    await page.click('button[type="submit"]');

    await expect(page.getByText("Company name is required.")).not.toBeVisible();
    await expect(page.getByText("Website URL is required.")).toBeVisible();
  });

  test("shows invalid URL error for malformed URL", async ({ page }) => {
    await page.goto("/");
    await page.fill("#company_name", "Acme");
    await page.fill("#website_url", "not-a-url");
    await page.click('button[type="submit"]');

    await expect(page.getByText("Enter a valid URL (http:// or https://).")).toBeVisible();
  });

  test("shows invalid URL error for URL without protocol", async ({ page }) => {
    await page.goto("/");
    await page.fill("#company_name", "Acme");
    await page.fill("#website_url", "example.com");
    await page.click('button[type="submit"]');

    await expect(page.getByText("Enter a valid URL (http:// or https://).")).toBeVisible();
  });
});

