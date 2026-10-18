// DATABASE_URL must point to a migrated, explicitly seeded disposable PostgreSQL database.
if (!process.env.DATABASE_URL) throw new Error("Set DATABASE_URL and run Alembic + Evergreen seed before E2E tests.");

import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  use: { baseURL: "https://127.0.0.1:4173", trace: "retain-on-failure", ignoreHTTPSErrors: true },
  projects: [
    {
      name: "desktop",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 1100 },
      },
    },
    {
      name: "narrow",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 390, height: 844 },
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
