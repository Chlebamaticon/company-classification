import { defineConfig } from "@playwright/test";

const REAL_BASE_URL = process.env.E2E_BASE_URL || "http://localhost:5173";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  use: {
    baseURL: "http://localhost:5173",
    headless: true,
  },
  webServer: [
    {
      command: "VITE_USE_MOCK=true npx vite --port 5173",
      port: 5173,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npx vite --port 5174",
      port: 5174,
      reuseExistingServer: !process.env.CI,
    },
  ],
  projects: [
    {
      name: "mock",
      testMatch: /happy-path|unhappy-path\.spec/,
      use: { browserName: "chromium", baseURL: "http://localhost:5173" },
    },
    {
      name: "real-api",
      testMatch: /server-error\.spec/,
      use: { browserName: "chromium", baseURL: "http://localhost:5174" },
    },
    {
      name: "real",
      testMatch: /real-product\.spec/,
      timeout: 120_000,
      use: { browserName: "chromium", baseURL: REAL_BASE_URL },
    },
  ],
});
