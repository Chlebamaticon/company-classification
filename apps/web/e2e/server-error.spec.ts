import { test, expect } from "@playwright/test";

test.describe("Server error handling", () => {
  test("shows error banner on submission failure and dismiss resets form", async ({ page }) => {
    await page.route("**/api/submissions", (route) =>
      route.fulfill({ status: 500, body: "Internal Server Error" }),
    );

    await page.goto("/");

    await page.fill("#company_name", "Acme");
    await page.fill("#website_url", "https://acme.com");
    await page.click('button[type="submit"]');

    await expect(page.getByText(/Submission failed \(500\)/)).toBeVisible({ timeout: 5_000 });

    await page.click("text=Dismiss");

    await expect(page.locator("#company_name")).toBeVisible();
    await expect(page.getByText(/Submission failed/)).not.toBeVisible();
  });

  test("shows error banner on network failure", async ({ page }) => {
    await page.route("**/api/submissions", (route) => route.abort("connectionrefused"));

    await page.goto("/");

    await page.fill("#company_name", "Acme");
    await page.fill("#website_url", "https://acme.com");
    await page.click('button[type="submit"]');

    await expect(page.locator(".text-red-700")).toBeVisible({ timeout: 5_000 });
  });
});
