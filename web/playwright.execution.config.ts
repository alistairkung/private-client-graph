import { defineConfig } from "@playwright/test";
import history from "./playwright.research.config";
export default defineConfig({
  ...history,
  testDir: "./research-execution-e2e",
  workers: 1,
  webServer: {
    command: "../.venv/bin/python ../tests/research_browser_server.py",
    url: "http://127.0.0.1:4175/health",
    reuseExistingServer: false,
    env: { PCG_BROWSER_EXECUTION: "1" },
  },
});
