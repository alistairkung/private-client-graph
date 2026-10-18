import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  expect: { timeout: 10000 },
  use: {
    baseURL: "https://127.0.0.1:5443",
    ignoreHTTPSErrors: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "desktop",
      use: { browserName: "chromium", viewport: { width: 1512, height: 982 } },
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
  webServer: [
    {
      command: "npm run backend:synthetic",
      url: "http://127.0.0.1:8001/health",
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
    },
    {
      command: "npm run dev",
      url: "https://127.0.0.1:5443",
      ignoreHTTPSErrors: true,
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
    },
  ],
});
