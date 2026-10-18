// DATABASE_URL must point to a migrated, explicitly seeded disposable PostgreSQL database.
if (!process.env.DATABASE_URL) throw new Error("Set DATABASE_URL and run Alembic + Evergreen seed before E2E tests.");

import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 2,
  timeout: 45000,
  expect: { timeout: 10000 },
  use: { baseURL: "https://127.0.0.1:4173", trace: "retain-on-failure", screenshot: "only-on-failure", ignoreHTTPSErrors: true },
  projects: [
    {
      name: "desktop",
      use: {
        browserName: "chromium",
        viewport: { width: 1512, height: 982 },
      },
    },
    {
      name: "phone",
      testIgnore: "**/api-contract.spec.ts",
      use: {
        browserName: "chromium",
        viewport: { width: 390, height: 844 },
        isMobile: true,
        hasTouch: true,
      },
    },
  ],
  webServer: [{
    command:
      "../.venv/bin/python ../tests/practitioner_browser_server.py",
    url: "https://127.0.0.1:4173/health",
    reuseExistingServer: false,
    ignoreHTTPSErrors: true,
  }],
});
