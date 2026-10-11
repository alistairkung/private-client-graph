import { defineConfig, devices } from "@playwright/test";
if (!process.env.DATABASE_URL)
  throw new Error(
    "Set DATABASE_URL to a migrated disposable PostgreSQL database.",
  );
export default defineConfig({
  testDir: "./research-e2e",
  use: { baseURL: "http://127.0.0.1:4175", trace: "retain-on-failure" },
  projects: [
    {
      name: "research-desktop",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 1100 },
      },
    },
    {
      name: "research-compact",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1024, height: 900 },
      },
    },
    {
      name: "research-narrow",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 390, height: 844 },
      },
    },
  ],
  webServer: {
    command: "../.venv/bin/python ../tests/research_browser_server.py",
    url: "http://127.0.0.1:4175/health",
    reuseExistingServer: false,
  },
});
