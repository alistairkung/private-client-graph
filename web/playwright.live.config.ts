import { defineConfig } from "@playwright/test";
import execution from "./playwright.execution.config";
export default defineConfig({
  ...execution,
  testDir: "./research-live-e2e",
  webServer: {
    command: "../.venv/bin/python ../tests/research_browser_server.py",
    url: "http://127.0.0.1:4175/health",
    reuseExistingServer: false,
    env: { PCG_BROWSER_EXECUTION: "1", PCG_BROWSER_LIVE: "1" },
  },
});
